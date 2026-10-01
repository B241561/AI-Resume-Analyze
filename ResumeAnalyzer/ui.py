from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from tkinter import BooleanVar, filedialog, messagebox
from typing import Any

import customtkinter as ctk

from analyzer import analyze_resume, groq_error_message, test_groq_connection
from config import (
    ASSETS_DIR,
    get_groq_api_key,
    get_groq_key_source,
    get_stored_groq_api_key,
    remove_stored_groq_api_key,
    save_groq_api_key,
)
from database import list_recent_analyses, save_analysis
from pdf_reader import PdfReadError, extract_text_from_file
from report_generator import export_analysis_pdf


logger = logging.getLogger(__name__)


def run_groq_connection_test(api_key: str) -> tuple[bool, str]:
    """Run the Groq connection test and return (ok, safe_message).

    Only sanitized category messages are returned; raw exception text is never exposed.
    """
    try:
        test_groq_connection(api_key)
    except Exception as exc:
        return False, groq_error_message(exc)
    return True, "Groq connection successful."


def save_groq_key_checked(api_key: str) -> bool:
    """Save the key and confirm it can actually be read back from secure storage."""
    cleaned = (api_key or "").strip()
    if not cleaned:
        return False
    try:
        save_groq_api_key(cleaned)
    except ValueError:
        return False
    except Exception:
        return False
    return get_stored_groq_api_key() == cleaned


class ResumeAnalyzerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Resume Analyzer")
        self.geometry("1180x790")
        self.minsize(980, 680)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.selected_file: Path | None = None
        self.current_analysis: dict[str, Any] | None = None
        self.current_file_name = ""
        self.use_groq_var = BooleanVar(value=bool(get_groq_api_key()))

        self._set_icon()
        self._build_layout()
        self._load_history()

    def _set_icon(self) -> None:
        icon_path = ASSETS_DIR / "app_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                logger.warning("Could not load application icon.")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=330, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(5, weight=1)

        title = ctk.CTkLabel(sidebar, text="AI Resume Analyzer", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, padx=22, pady=(24, 8), sticky="w")

        subtitle = ctk.CTkLabel(sidebar, text="PDF/DOCX + scanned PDF OCR", text_color="#94A3B8")
        subtitle.grid(row=1, column=0, padx=22, pady=(0, 18), sticky="w")

        self.file_label = ctk.CTkLabel(sidebar, text="No PDF or DOCX selected", anchor="w", wraplength=270)
        self.file_label.grid(row=2, column=0, padx=22, pady=(0, 10), sticky="ew")

        pick_button = ctk.CTkButton(sidebar, text="Choose Resume File", command=self._choose_resume_file)
        pick_button.grid(row=3, column=0, padx=22, pady=(0, 18), sticky="ew")

        history_title = ctk.CTkLabel(sidebar, text="Previous Analyses", font=ctk.CTkFont(size=16, weight="bold"))
        history_title.grid(row=4, column=0, padx=22, pady=(0, 8), sticky="sw")

        self.history_box = ctk.CTkTextbox(sidebar, height=180, activate_scrollbars=True)
        self.history_box.grid(row=5, column=0, padx=22, pady=(0, 22), sticky="nsew")
        self.history_box.configure(state="disabled")

        about_button = ctk.CTkButton(sidebar, text="About", command=self._show_about_dialog)
        about_button.grid(row=6, column=0, padx=22, pady=(0, 22), sticky="ew")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)

        input_card = ctk.CTkFrame(content)
        input_card.grid(row=0, column=0, sticky="ew")
        input_card.grid_columnconfigure(0, weight=1)

        jd_label = ctk.CTkLabel(input_card, text="Optional Job Description", font=ctk.CTkFont(size=16, weight="bold"))
        jd_label.grid(row=0, column=0, padx=18, pady=(16, 8), sticky="w")

        self.job_textbox = ctk.CTkTextbox(input_card, height=110)
        self.job_textbox.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")

        self.groq_notice = ctk.CTkLabel(
            input_card,
            text="",
            text_color="#94A3B8",
            wraplength=760,
            justify="left",
        )
        self.groq_notice.grid(row=2, column=0, padx=18, pady=(0, 8), sticky="w")

        self.groq_checkbox = ctk.CTkCheckBox(
            input_card,
            text="Use Groq AI for contextual feedback and job matching",
            variable=self.use_groq_var,
            onvalue=True,
            offvalue=False,
            command=self._update_groq_notice,
        )
        self.groq_checkbox.grid(row=3, column=0, padx=18, pady=(0, 12), sticky="w")

        groq_settings_row = ctk.CTkFrame(input_card, fg_color="transparent")
        groq_settings_row.grid(row=4, column=0, padx=18, pady=(0, 12), sticky="ew")
        groq_settings_row.grid_columnconfigure(0, weight=1)
        self.groq_status_label = ctk.CTkLabel(groq_settings_row, text="")
        self.groq_status_label.grid(row=0, column=0, sticky="w")
        self.groq_configure_button = ctk.CTkButton(
            groq_settings_row,
            text="Configure API Key",
            width=150,
            command=self._show_groq_settings,
        )
        self.groq_configure_button.grid(row=0, column=1, padx=(8, 0), sticky="e")
        self.groq_remove_button = ctk.CTkButton(
            groq_settings_row,
            text="Remove API Key",
            width=130,
            fg_color="transparent",
            border_width=1,
            command=self._remove_groq_key,
        )
        self._refresh_groq_state()

        action_row = ctk.CTkFrame(input_card, fg_color="transparent")
        action_row.grid(row=5, column=0, padx=18, pady=(0, 16), sticky="ew")
        action_row.grid_columnconfigure(3, weight=1)

        self.analyze_button = ctk.CTkButton(action_row, text="Analyze Resume", command=self._start_analysis)
        self.analyze_button.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.export_button = ctk.CTkButton(
            action_row, text="Download Report", command=self._export_report, state="disabled"
        )
        self.export_button.grid(row=0, column=1, padx=(0, 10), sticky="w")

        self.json_button = ctk.CTkButton(
            action_row, text="Download JSON", command=self._export_json, state="disabled"
        )
        self.json_button.grid(row=0, column=2, padx=(0, 10), sticky="w")

        self.progress = ctk.CTkProgressBar(action_row, mode="indeterminate")
        self.progress.grid(row=0, column=3, sticky="ew")
        self.progress.stop()
        self.progress.grid_remove()

        scores = ctk.CTkFrame(content, fg_color="transparent")
        scores.grid(row=1, column=0, pady=16, sticky="ew")
        scores.grid_columnconfigure((0, 1), weight=1)

        self.ats_card = ScoreCard(scores, "ATS Readiness")
        self.ats_card.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.match_card = ScoreCard(scores, "Job Match")
        self.match_card.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        self.match_card.set_score(None)

        self.results_frame = ctk.CTkScrollableFrame(content)
        self.results_frame.grid(row=2, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure((0, 1), weight=1)
        self._show_empty_state()

    def _choose_resume_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose Resume File",
            filetypes=[
                ("Resume Files", "*.pdf *.docx"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx"),
            ],
        )
        if not path:
            return
        self.selected_file = Path(path)
        self.file_label.configure(text=self.selected_file.name)

    def _start_analysis(self) -> None:
        if not self.selected_file:
            messagebox.showwarning("Resume required", "Please choose a PDF or DOCX resume first.")
            return

        resume_path = self.selected_file
        job_description = self.job_textbox.get("1.0", "end").strip()
        use_groq = bool(self.use_groq_var.get()) and bool(get_groq_api_key())
        self.current_analysis = None
        self.current_file_name = ""
        self._set_busy(True)
        thread = threading.Thread(
            target=self._run_analysis,
            args=(resume_path, job_description, use_groq),
            daemon=True,
        )
        thread.start()

    def _run_analysis(self, resume_path: Path, job_description: str, use_groq: bool) -> None:
        try:
            resume_text = extract_text_from_file(resume_path)
            analysis = analyze_resume(resume_text, job_description, use_groq=use_groq)
            analysis_id = save_analysis(resume_path, resume_text, job_description, analysis)
            analysis["id"] = analysis_id
            self.after(0, lambda: self._analysis_completed(resume_path.name, analysis))
        except PdfReadError as exc:
            message = str(exc)
            self.after(0, lambda: self._show_error(message))
        except Exception:
            logger.exception("Analysis failed")
            self.after(0, lambda: self._show_error("Analysis failed. Check logs/app.log for details."))

    def _analysis_completed(self, file_name: str, analysis: dict[str, Any]) -> None:
        self.current_file_name = file_name
        self.current_analysis = analysis
        self._set_busy(False)
        self._render_analysis(analysis)
        self._load_history()

    def _show_error(self, message: str) -> None:
        self._set_busy(False)
        messagebox.showerror("Error", message)

    def _update_groq_notice(self) -> None:
        if not get_groq_api_key():
            notice = (
                "Groq is unavailable. No resume or job-description text is sent. "
                "Local analysis remains available."
            )
        elif self.use_groq_var.get():
            notice = (
                "Groq sends extracted resume and job-description text to its AI API "
                "for AI-assisted analysis when enabled."
            )
        else:
            notice = "No resume or job-description text is sent to Groq while Groq is OFF."
        self.groq_notice.configure(text=notice)

    def _refresh_groq_state(self, enabled: bool | None = None) -> None:
        configured = bool(get_groq_api_key())
        source = get_groq_key_source()
        self.groq_checkbox.configure(state="normal" if configured else "disabled")
        self.use_groq_var.set(configured if enabled is None else bool(enabled and configured))
        if configured:
            source_label = "secure storage" if source == "secure storage" else "GROQ_API_KEY"
            self.groq_status_label.configure(
                text=f"Groq AI  ● Configured via {source_label}", text_color="#86EFAC"
            )
            self.groq_configure_button.configure(text="Change API Key")
        else:
            self.groq_status_label.configure(
                text="Groq AI  ○ Not configured", text_color="#94A3B8"
            )
            self.groq_configure_button.configure(text="Configure API Key")
        has_stored_key = bool(get_stored_groq_api_key())
        if configured:
            self.groq_remove_button.grid(row=0, column=2, padx=(8, 0), sticky="e")
            self.groq_remove_button.configure(state="normal" if has_stored_key else "disabled")
        else:
            self.groq_remove_button.grid_remove()
        self._update_groq_notice()

    def _show_groq_settings(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Groq AI Settings")
        dialog.geometry("480x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog, text="Groq AI Settings", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=24, pady=(22, 14), sticky="w")

        current_key = get_groq_api_key()
        if current_key:
            # Never display any part of the actual API key.
            masked_key = "•" * 16
            current_text = f"Current key ({get_groq_key_source()}): {masked_key}"
        else:
            current_text = "No API key is configured."

        ctk.CTkLabel(dialog, text=current_text, text_color="#94A3B8").grid(
            row=1, column=0, padx=24, pady=(0, 12), sticky="w"
        )

        entry_row = ctk.CTkFrame(dialog, fg_color="transparent")
        entry_row.grid(row=2, column=0, padx=24, sticky="ew")
        entry_row.grid_columnconfigure(0, weight=1)

        key_entry = ctk.CTkEntry(
            entry_row, placeholder_text="Enter a new API key", show="•", height=36
        )
        key_entry.grid(row=0, column=0, sticky="ew")
        show_state = {"visible": False}

        def toggle_visibility() -> None:
            show_state["visible"] = not show_state["visible"]
            key_entry.configure(show="" if show_state["visible"] else "•")
            show_button.configure(text="Hide" if show_state["visible"] else "Show")

        show_button = ctk.CTkButton(
            entry_row, text="Show", width=64, command=toggle_visibility
        )
        show_button.grid(row=0, column=1, padx=(8, 0))

        def test_connection() -> None:
            candidate = key_entry.get().strip() or current_key
            if not candidate:
                messagebox.showwarning(
                    "API key required",
                    "Enter an API key before testing the connection.",
                    parent=dialog,
                )
                return

            test_button.configure(state="disabled", text="Testing...")
            dialog.update_idletasks()

            try:
                ok, message = run_groq_connection_test(candidate)
            finally:
                test_button.configure(state="normal", text="Test Connection")

            if ok:
                messagebox.showinfo("Connection successful", message, parent=dialog)
            else:
                messagebox.showerror("Connection failed", message, parent=dialog)

        def save_key() -> None:
            candidate = key_entry.get().strip()
            if not candidate:
                messagebox.showwarning(
                    "API key required",
                    "Enter an API key to save.",
                    parent=dialog,
                )
                return

            if not save_groq_key_checked(candidate):
                messagebox.showerror(
                    "Save failed",
                    "Could not save the API key to the operating system credential store.",
                    parent=dialog,
                )
                return

            self._refresh_groq_state(enabled=True)
            messagebox.showinfo("Key saved", "API key saved securely.", parent=dialog)
            dialog.destroy()

        button_row = ctk.CTkFrame(dialog, fg_color="transparent")
        button_row.grid(row=3, column=0, padx=24, pady=(24, 22), sticky="e")

        test_button = ctk.CTkButton(
            button_row, text="Test Connection", command=test_connection
        )
        test_button.grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            button_row, text="Save", command=save_key
        ).grid(row=0, column=1, padx=(0, 8))

        ctk.CTkButton(
            button_row,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            command=dialog.destroy,
        ).grid(row=0, column=2)

        key_entry.bind("<Return>", lambda _event: save_key())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        key_entry.focus_set()

    def _remove_groq_key(self) -> None:
        if not get_stored_groq_api_key():
            return
        if not messagebox.askyesno(
            "Remove API key", "Remove the Groq API key from this device's secure credential store?"
        ):
            return
        try:
            remove_stored_groq_api_key()
        except Exception:
            messagebox.showerror(
                "Remove failed", "Could not remove the stored API key from the credential store."
            )
            return
        fallback_available = bool(get_groq_api_key())
        self._refresh_groq_state(enabled=fallback_available)
        if fallback_available:
            messagebox.showinfo(
                "Key removed", "The stored key was removed. GROQ_API_KEY remains configured."
            )
        else:
            messagebox.showinfo("Key removed", "The stored Groq API key was removed.")

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self.analyze_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.json_button.configure(state="disabled")
            self.groq_checkbox.configure(state="disabled")
            self.progress.grid()
            self.progress.start()
        else:
            self.analyze_button.configure(state="normal")
            self.groq_checkbox.configure(
                state="normal" if get_groq_api_key() else "disabled"
            )
            self.progress.stop()
            self.progress.grid_remove()
            download_state = "normal" if self.current_analysis else "disabled"
            self.export_button.configure(state=download_state)
            self.json_button.configure(state=download_state)

    def _render_analysis(self, analysis: dict[str, Any]) -> None:
        self._clear_results()
        self.ats_card.set_score(int(analysis.get("ats_score", 0)))
        self.match_card.set_score(
            analysis.get("match_percentage"), analysis.get("match_method", "")
        )

        SummaryCard(self.results_frame, "Analysis Mode", analysis.get("analysis_mode", "Local analysis")).grid(
            row=0, column=0, columnspan=2, padx=6, pady=6, sticky="ew"
        )

        SummaryCard(self.results_frame, "Resume Summary", analysis.get("summary", "")).grid(
            row=1, column=0, columnspan=2, padx=6, pady=6, sticky="ew"
        )

        breakdown = analysis.get("ats_breakdown", {})
        BreakdownCard(self.results_frame, "ATS Readiness Breakdown", breakdown).grid(
            row=2, column=0, columnspan=2, padx=6, pady=6, sticky="ew"
        )

        if analysis.get("match_explanation"):
            SummaryCard(self.results_frame, "Job Match Method", analysis["match_explanation"]).grid(
                row=3, column=0, columnspan=2, padx=6, pady=6, sticky="ew"
            )

        match_available = analysis.get(
            "match_available", analysis.get("match_percentage") is not None
        )
        missing_keywords = analysis.get("missing_keywords", [])
        missing_job_skills = analysis.get("missing_job_skills", [])
        if not match_available:
            missing_keywords = ["Add a job description to compare keywords."]
            missing_job_skills = ["Add a job description to compare required skills."]

        cards = [
            ("Technical Skills", analysis.get("technical_skills", [])),
            ("Soft Skills", analysis.get("soft_skills", [])),
            ("Missing Skills", analysis.get("missing_skills", [])),
            ("Strengths", analysis.get("strengths", [])),
            ("Weaknesses", analysis.get("weaknesses", [])),
            ("Grammar Suggestions", analysis.get("grammar_suggestions", [])),
            ("Missing Keywords", missing_keywords),
            ("Missing Job Skills", missing_job_skills),
        ]

        start_row = 4 if analysis.get("match_explanation") else 3
        for position, (title, items) in enumerate(cards):
            row = start_row + position // 2
            column = position % 2
            ListCard(self.results_frame, title, items).grid(row=row, column=column, padx=6, pady=6, sticky="nsew")

        recommendations_row = start_row + (len(cards) + 1) // 2
        RecommendationsCard(self.results_frame, analysis.get("recommendations", [])).grid(
            row=recommendations_row, column=0, columnspan=2, padx=6, pady=6, sticky="ew"
        )

    def _show_empty_state(self) -> None:
        self._clear_results()
        label = ctk.CTkLabel(
            self.results_frame,
            text="Choose a resume PDF/DOCX and click Analyze Resume.",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#CBD5E1",
        )
        label.grid(row=0, column=0, padx=24, pady=80, sticky="ew")

    def _clear_results(self) -> None:
        for child in self.results_frame.winfo_children():
            child.destroy()

    def _suggested_download_name(self, extension: str) -> str:
        resume_stem = Path(self.current_file_name).stem or "Resume"
        return f"{resume_stem}_AI_Resume_Analysis{extension}"

    def _export_report(self) -> None:
        if not self.current_analysis:
            messagebox.showwarning("No analysis", "Analyze a resume before exporting.")
            return
        destination = filedialog.asksaveasfilename(
            title="Download PDF Report",
            defaultextension=".pdf",
            initialfile=self._suggested_download_name(".pdf"),
            filetypes=[("PDF documents", "*.pdf")],
            confirmoverwrite=True,
        )
        if not destination:
            return
        try:
            output_path = export_analysis_pdf(
                self.current_file_name, self.current_analysis, Path(destination)
            )
            messagebox.showinfo("Report exported", f"Saved report to:\n{output_path}")
        except Exception:
            logger.exception("Report export failed")
            messagebox.showerror("Export failed", "Could not export the PDF report.")

    def _export_json(self) -> None:
        if not self.current_analysis:
            messagebox.showwarning("No analysis", "Analyze a resume before exporting.")
            return
        destination = filedialog.asksaveasfilename(
            title="Download JSON Results",
            defaultextension=".json",
            initialfile=self._suggested_download_name(".json"),
            filetypes=[("JSON files", "*.json")],
            confirmoverwrite=True,
        )
        if not destination:
            return
        try:
            payload = dict(self.current_analysis)
            payload["resume_file"] = self.current_file_name
            Path(destination).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            messagebox.showinfo("Results downloaded", f"Saved JSON results to:\n{destination}")
        except Exception:
            logger.exception("JSON export failed")
            messagebox.showerror("Export failed", "Could not save the JSON results.")

    def _load_history(self) -> None:
        history = list_recent_analyses()
        lines = []
        for item in history:
            match = "—" if item.get("match_percentage") is None else f"{item['match_percentage']}%"
            lines.append(
                f"#{item['id']}  {item['file_name']}\nATS: {item['ats_score']} | Match: {match}\n"
            )
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.insert("1.0", "\n".join(lines) if lines else "No saved analyses yet.")
        self.history_box.configure(state="disabled")

    def _show_about_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("About AI Resume Analyzer")
        dialog.geometry("600x700")
        dialog.minsize(540, 620)
        dialog.transient(self)
        dialog.grab_set()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(dialog)
        container.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            container,
            text="AI Resume Analyzer",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(8, 4), sticky="w")

        details = (
            "Project Name: AI Resume Analyzer\n"
            "Version: 2.0\n"
            "Developer: Arman Kaushik\n"
            "Course: B.Tech Computer Science and Engineering (CSE)\n"
            "College: Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur\n"
            "Semester: Vth Semester\n"
            "Project Type: AI-powered desktop application"
        )
        ctk.CTkLabel(container, text=details, justify="left", anchor="w", wraplength=520).grid(
            row=1, column=0, padx=12, pady=(8, 12), sticky="ew"
        )

        description = (
            "AI Resume Analyzer processes PDF and DOCX resumes, extracts text (including scanned PDFs through Tesseract OCR), "
            "and provides ATS-oriented readiness scoring, technical and soft-skill extraction, job-description matching, and "
            "practical improvement recommendations. Analysis runs locally by default with a deterministic fallback; optional "
            "Groq assistance adds contextual feedback and job matching. Analysis history is stored in local SQLite without "
            "retaining raw resume or job-description text, and results can be exported as PDF reports."
        )
        ctk.CTkLabel(
            container,
            text="Project Description",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=2, column=0, padx=12, pady=(12, 4), sticky="w")
        ctk.CTkLabel(container, text=description, wraplength=520, justify="left").grid(
            row=3, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

        privacy = (
            "Privacy: raw resume text and job descriptions are not stored in the local SQLite history. "
            "When Groq is enabled, the extracted text is sent to the configured Groq API; when disabled, analysis remains local."
        )
        ctk.CTkLabel(
            container,
            text="Privacy",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=4, column=0, padx=12, pady=(12, 4), sticky="w")
        ctk.CTkLabel(container, text=privacy, wraplength=520, justify="left").grid(
            row=5, column=0, padx=12, pady=(0, 12), sticky="ew"
        )

        references = "\n".join(
            [
                "- Groq API\n  https://console.groq.com/",
                "- Python\n  https://docs.python.org/",
                "- CustomTkinter\n  https://customtkinter.tomschimansky.com/",
                "- PyMuPDF\n  https://pymupdf.readthedocs.io/",
                "- python-docx\n  https://python-docx.readthedocs.io/",
                "- SQLite\n  https://sqlite.org/",
                "- ReportLab\n  https://www.reportlab.com/",
                "- Tesseract OCR\n  https://github.com/tesseract-ocr/tesseract",
                "- scikit-learn\n  https://scikit-learn.org/",
            ]
        )
        ctk.CTkLabel(
            container,
            text="References",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=6, column=0, padx=12, pady=(12, 4), sticky="w")
        ctk.CTkLabel(container, text=references, justify="left").grid(
            row=7, column=0, padx=12, pady=(0, 12), sticky="w"
        )

        ctk.CTkButton(container, text="Close", command=dialog.destroy).grid(
            row=8, column=0, padx=12, pady=(0, 12), sticky="e"
        )


class ScoreCard(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, title: str) -> None:
        super().__init__(parent)
        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=15, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=18, pady=(16, 4), sticky="w")

        self.score_font = ctk.CTkFont(size=36, weight="bold")
        self.empty_score_font = ctk.CTkFont(size=30, weight="bold")
        self.score_label = ctk.CTkLabel(self, text="0", font=self.score_font)
        self.score_label.grid(row=1, column=0, padx=18, pady=(0, 8), sticky="w")

        self.detail_label = ctk.CTkLabel(
            self, text="", text_color="#94A3B8", font=ctk.CTkFont(size=12), wraplength=340, justify="left"
        )
        self.detail_label.grid(row=2, column=0, padx=18, pady=(0, 8), sticky="w")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=3, column=0, padx=18, pady=(0, 18), sticky="ew")
        self.grid_columnconfigure(0, weight=1)
        self.set_score(0)

    def set_score(self, score: int | None, detail: str = "") -> None:
        if score is None:
            self.score_label.configure(text="— / 100", font=self.empty_score_font)
            self.detail_label.configure(
                text="No job description provided. Add one to calculate match."
            )
            self.progress.set(0)
            return

        score = max(0, min(100, score))
        self.score_label.configure(text=f"{score}/100", font=self.score_font)
        self.detail_label.configure(text=detail)
        self.progress.set(score / 100)


class SummaryCard(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, title: str, text: str) -> None:
        super().__init__(parent)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 8), sticky="w"
        )
        ctk.CTkLabel(self, text=text or "No summary available.", wraplength=760, justify="left").grid(
            row=1, column=0, padx=16, pady=(0, 14), sticky="ew"
        )
        self.grid_columnconfigure(0, weight=1)


class BreakdownCard(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, title: str, breakdown: dict[str, Any]) -> None:
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 8), sticky="w"
        )
        labels = {
            "contact_and_links": "Contact & links",
            "resume_sections": "Resume sections",
            "technical_skills": "Technical skills",
            "measurable_impact": "Measurable impact",
            "action_language": "Action language",
            "parseability": "Parseability",
            "job_relevance": "Job relevance",
        }
        text = " | ".join(
            f"{labels.get(key, key.replace('_', ' ').title())}: {value}"
            for key, value in breakdown.items()
        ) or "No breakdown available."
        ctk.CTkLabel(self, text=text, wraplength=760, justify="left", text_color="#CBD5E1").grid(
            row=1, column=0, padx=14, pady=(0, 14), sticky="w"
        )


class ListCard(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, title: str, items: list[str]) -> None:
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 8), sticky="w"
        )
        body = "\n".join(f"- {item}" for item in items) if items else "No items available."
        ctk.CTkLabel(self, text=body, wraplength=390, justify="left").grid(
            row=1, column=0, padx=14, pady=(0, 14), sticky="nw"
        )


class RecommendationsCard(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, recommendations: list[str]) -> None:
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text="RECOMMENDATIONS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#93C5FD",
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")
        items = recommendations or ["Tailor quantified achievements and relevant skills to each target role."]
        body = "\n\n".join(f"{position}. {item}" for position, item in enumerate(items, start=1))
        ctk.CTkLabel(self, text=body, wraplength=760, justify="left").grid(
            row=1, column=0, padx=16, pady=(0, 14), sticky="nw"
        )
