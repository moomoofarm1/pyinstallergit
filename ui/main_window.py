"""
Main Window for ALF Audio Processing Application

This module provides the main tkinter-based user interface for controlling
the audio processing pipeline including diarization and transcription workflows.

The interface allows users to:
- Preprocess audio files (MP3 to 16KHz mono)
- Run speaker diarization with pyannote.audio
- Perform speech transcription with NeMo ASR
- Manage Label Studio frontend instances
- Monitor processing status and logs
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
import os
from pathlib import Path
from typing import Optional, List

from communication.server_manager import ServerManager
from communication.json_protocol import JsonProtocol
from ui.pipeline_controller import PipelineController
from audio_processing.preprocessing import AudioPreprocessor

logger = logging.getLogger(__name__)

class AudioProcessingApp:
    """
    Main application class for the ALF audio processing interface.
    
    This class manages the tkinter GUI and coordinates between different
    processing pipelines, server management, and user interactions.
    """
    
    def __init__(self):
        """Initialize the main application window and components."""
        self.root = tk.Tk()
        self.root.title("ALF - Advanced Audio Label Frontend v0.2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Application state
        self.current_audio_file: Optional[str] = None
        self.processed_files: List[str] = []
        
        # Core components
        self.server_manager = ServerManager()
        self.json_protocol = JsonProtocol()
        self.pipeline_controller = PipelineController(self.server_manager, self.json_protocol)
        self.audio_preprocessor = AudioPreprocessor()
        
        # GUI components
        self.setup_ui()
        self.setup_logging_display()
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("AudioProcessingApp initialized")
    
    def setup_ui(self):
        """Set up the main user interface components."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title and status
        title_label = ttk.Label(main_frame, text="ALF - Advanced Audio Label Frontend", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        self.status_var = tk.StringVar(value="Ready - Please select an audio file to begin")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # File selection section
        self.setup_file_section(main_frame, row=2)
        
        # Pipeline control section
        self.setup_pipeline_section(main_frame, row=3)
        
        # Log display section (takes remaining space)
        self.setup_log_section(main_frame, row=4)
        
        # Progress bar
        self.progress_var = tk.StringVar()
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_file_section(self, parent: ttk.Frame, row: int):
        """Set up the file selection and preprocessing section."""
        file_frame = ttk.LabelFrame(parent, text="Audio File Management", padding="10")
        file_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File selection
        ttk.Label(file_frame, text="Selected File:").grid(row=0, column=0, sticky=tk.W)
        self.file_var = tk.StringVar(value="No file selected")
        file_label = ttk.Label(file_frame, textvariable=self.file_var, relief="sunken", 
                              background="white", foreground="black")
        file_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        select_btn = ttk.Button(file_frame, text="Select MP3 File", command=self.select_audio_file)
        select_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Preprocessing controls
        preprocess_btn = ttk.Button(file_frame, text="Preprocess Audio (16KHz Mono)", 
                                   command=self.preprocess_audio)
        preprocess_btn.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
        
        self.preprocess_status_var = tk.StringVar(value="")
        preprocess_status = ttk.Label(
            file_frame,
            textvariable=self.preprocess_status_var,
            foreground="green"
        )
        preprocess_status.grid(row=1, column=1, columnspan=2, pady=(10, 0), sticky=tk.W, padx=(10, 0))
    
    def setup_pipeline_section(self, parent: ttk.Frame, row: int):
        """Set up the pipeline control section."""
        pipeline_frame = ttk.LabelFrame(parent, text="Processing Pipelines", padding="10")
        pipeline_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create notebook for different pipelines
        notebook = ttk.Notebook(pipeline_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        pipeline_frame.columnconfigure(0, weight=1)
        
        # Diarization tab
        diarization_frame = ttk.Frame(notebook, padding="10")
        notebook.add(diarization_frame, text="Speaker Diarization")
        self.setup_diarization_controls(diarization_frame)
        
        # Transcription tab
        transcription_frame = ttk.Frame(notebook, padding="10")
        notebook.add(transcription_frame, text="Speech Transcription")
        self.setup_transcription_controls(transcription_frame)
        
        # Environment management tab
        env_frame = ttk.Frame(notebook, padding="10")
        notebook.add(env_frame, text="Environment Management")
        self.setup_environment_controls(env_frame)
    
    def setup_diarization_controls(self, parent: ttk.Frame):
        """Set up diarization pipeline controls."""
        ttk.Label(parent, text="Speaker Diarization using pyannote.audio", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Server controls
        self.diarization_server_btn = ttk.Button(parent, text="Start Diarization Server", 
                                               command=self.toggle_diarization_server)
        self.diarization_server_btn.grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.diarization_browser_btn = ttk.Button(parent, text="Open Label Studio (Diarization)", 
                                                command=self.open_diarization_browser)
        self.diarization_browser_btn.grid(row=1, column=1, sticky=tk.W)
        
        # Processing controls
        run_diarization_btn = ttk.Button(parent, text="Run Diarization Pipeline", 
                                       command=self.run_diarization)
        run_diarization_btn.grid(row=2, column=0, pady=(10, 0), sticky=tk.W, padx=(0, 10))
        
        # Status display
        self.diarization_status_var = tk.StringVar(value="Server: Stopped | Browser: Not opened")
        diarization_status = ttk.Label(parent, textvariable=self.diarization_status_var, 
                                     foreground="red")
        diarization_status.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
    
    def setup_transcription_controls(self, parent: ttk.Frame):
        """Set up transcription pipeline controls."""
        ttk.Label(parent, text="Speech Transcription using NeMo ASR", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Server controls
        self.transcription_server_btn = ttk.Button(parent, text="Start Transcription Server", 
                                                 command=self.toggle_transcription_server)
        self.transcription_server_btn.grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.transcription_browser_btn = ttk.Button(parent, text="Open Label Studio (Transcription)", 
                                                  command=self.open_transcription_browser)
        self.transcription_browser_btn.grid(row=1, column=1, sticky=tk.W)
        
        # Processing controls
        run_transcription_btn = ttk.Button(parent, text="Run Transcription Pipeline", 
                                         command=self.run_transcription)
        run_transcription_btn.grid(row=2, column=0, pady=(10, 0), sticky=tk.W, padx=(0, 10))
        
        # Status display
        self.transcription_status_var = tk.StringVar(value="Server: Stopped | Browser: Not opened")
        transcription_status = ttk.Label(parent, textvariable=self.transcription_status_var, 
                                       foreground="red")
        transcription_status.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky=tk.W)
    
    def setup_environment_controls(self, parent: ttk.Frame):
        """Set up virtual environment management controls."""
        ttk.Label(parent, text="Virtual Environment Management", 
                 font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Environment status
        self.env_status_var = tk.StringVar(value="Checking environments...")
        env_status = ttk.Label(parent, textvariable=self.env_status_var)
        env_status.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        # Environment controls
        setup_env_btn = ttk.Button(parent, text="Setup All Environments", 
                                 command=self.setup_environments)
        setup_env_btn.grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        
        check_env_btn = ttk.Button(parent, text="Check Environment Status", 
                                 command=self.check_environments)
        check_env_btn.grid(row=2, column=1, sticky=tk.W)
        
        # Cleanup buttons
        cleanup_btn = ttk.Button(parent, text="Cleanup All Servers", 
                               command=self.cleanup_all_servers)
        cleanup_btn.grid(row=3, column=0, pady=(20, 0), sticky=tk.W, padx=(0, 10))
        
        # Exit button with full cleanup
        exit_btn = ttk.Button(parent, text="Exit ALF (Remove Environments)", 
                            command=self.exit_application_with_cleanup,
                            style="Accent.TButton")
        exit_btn.grid(row=3, column=1, pady=(20, 0), sticky=tk.W)
    
    def setup_log_section(self, parent: ttk.Frame, row: int):
        """Set up the log display section."""
        log_frame = ttk.LabelFrame(parent, text="Application Logs", padding="5")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Text widget for logs with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled', 
                                                 wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear logs button
        clear_btn = ttk.Button(log_frame, text="Clear Logs", command=self.clear_logs)
        clear_btn.grid(row=1, column=0, pady=(5, 0), sticky=tk.W)
    
    def setup_logging_display(self):
        """Set up logging to display in the GUI."""
        # Create a custom handler that writes to the text widget
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state='normal')
                    self.text_widget.insert(tk.END, msg + '\\n')
                    self.text_widget.config(state='disabled')
                    self.text_widget.see(tk.END)
                # Schedule the GUI update
                self.text_widget.after(0, append)
        
        # Add the handler to the root logger
        text_handler = TextHandler(self.log_text)
        text_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(text_handler)
        
        logger.info("GUI logging initialized")
    
    # Event handler methods
    def select_audio_file(self):
        """Handle audio file selection."""
        file_path = filedialog.askopenfilename(
            title="Select MP3 Audio File",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        
        if file_path:
            self.current_audio_file = file_path
            self.file_var.set(os.path.basename(file_path))
            self.update_status(f"Selected: {os.path.basename(file_path)}")
            logger.info(f"Selected audio file: {file_path}")
    
    def preprocess_audio(self):
        """Handle audio preprocessing."""
        if not self.current_audio_file:
            messagebox.showwarning("No File Selected", "Please select an MP3 file first.")
            return
        
        def preprocess_task():
            self.show_progress("Preprocessing audio...")
            try:
                output_path = self.audio_preprocessor.preprocess_mp3_to_mono_16k(
                    self.current_audio_file
                )
                self.processed_files.append(output_path)
                
                self.root.after(0, lambda: self.preprocess_status_var.set(
                    f"✓ Preprocessed: {os.path.basename(output_path)}"
                ))
                self.root.after(0, lambda: self.update_status("Audio preprocessing completed"))
                logger.info(f"Audio preprocessing completed: {output_path}")
                
            except Exception as e:
                logger.error(f"Audio preprocessing failed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Preprocessing failed: {e}"))
            finally:
                self.root.after(0, self.hide_progress)
        
        threading.Thread(target=preprocess_task, daemon=True).start()
    
    def toggle_diarization_server(self):
        """Toggle diarization server on/off."""
        if self.server_manager.is_diarization_running():
            self.server_manager.stop_diarization_server()
            self.diarization_server_btn.config(text="Start Diarization Server")
            self.diarization_status_var.set("Server: Stopped | Browser: Not opened")
        else:
            def start_server():
                try:
                    self.server_manager.start_diarization_server()
                    self.root.after(0, lambda: self.diarization_server_btn.config(
                        text="Stop Diarization Server"
                    ))
                    self.root.after(0, lambda: self.diarization_status_var.set(
                        "Server: Running | Browser: Not opened"
                    ))
                except Exception as e:
                    logger.error(f"Failed to start diarization server: {e}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Failed to start server: {e}"
                    ))
            
            threading.Thread(target=start_server, daemon=True).start()
    
    def toggle_transcription_server(self):
        """Toggle transcription server on/off."""
        if self.server_manager.is_transcription_running():
            self.server_manager.stop_transcription_server()
            self.transcription_server_btn.config(text="Start Transcription Server")
            self.transcription_status_var.set("Server: Stopped | Browser: Not opened")
        else:
            def start_server():
                try:
                    self.server_manager.start_transcription_server()
                    self.root.after(0, lambda: self.transcription_server_btn.config(
                        text="Stop Transcription Server"
                    ))
                    self.root.after(0, lambda: self.transcription_status_var.set(
                        "Server: Running | Browser: Not opened"
                    ))
                except Exception as e:
                    logger.error(f"Failed to start transcription server: {e}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Failed to start server: {e}"
                    ))
            
            threading.Thread(target=start_server, daemon=True).start()
    
    def open_diarization_browser(self):
        """Open Label Studio browser for diarization."""
        try:
            self.pipeline_controller.open_diarization_browser()
            self.diarization_status_var.set("Server: Running | Browser: Opened")
            logger.info("Diarization browser opened")
        except Exception as e:
            logger.error(f"Failed to open diarization browser: {e}")
            messagebox.showerror("Error", f"Failed to open browser: {e}")
    
    def open_transcription_browser(self):
        """Open Label Studio browser for transcription."""
        try:
            self.pipeline_controller.open_transcription_browser()
            self.transcription_status_var.set("Server: Running | Browser: Opened")
            logger.info("Transcription browser opened")
        except Exception as e:
            logger.error(f"Failed to open transcription browser: {e}")
            messagebox.showerror("Error", f"Failed to open browser: {e}")
    
    def run_diarization(self):
        """Run the diarization pipeline."""
        if not self.processed_files:
            messagebox.showwarning("No Processed Audio", 
                                 "Please preprocess an audio file first.")
            return
        
        def diarization_task():
            self.show_progress("Running diarization...")
            try:
                result = self.pipeline_controller.run_diarization_pipeline(
                    self.processed_files[-1]  # Use the most recently processed file
                )
                logger.info(f"Diarization completed: {result}")
                self.root.after(0, lambda: self.update_status("Diarization completed"))
            except Exception as e:
                logger.error(f"Diarization failed: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Diarization failed: {e}"
                ))
            finally:
                self.root.after(0, self.hide_progress)
        
        threading.Thread(target=diarization_task, daemon=True).start()
    
    def run_transcription(self):
        """Run the transcription pipeline."""
        if not self.processed_files:
            messagebox.showwarning("No Processed Audio", 
                                 "Please preprocess an audio file first.")
            return
        
        def transcription_task():
            self.show_progress("Running transcription...")
            try:
                result = self.pipeline_controller.run_transcription_pipeline(
                    self.processed_files[-1]  # Use the most recently processed file
                )
                logger.info(f"Transcription completed: {result}")
                self.root.after(0, lambda: self.update_status("Transcription completed"))
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Transcription failed: {e}"
                ))
            finally:
                self.root.after(0, self.hide_progress)
        
        threading.Thread(target=transcription_task, daemon=True).start()
    
    def setup_environments(self):
        """Set up virtual environments."""
        def setup_task():
            self.show_progress("Setting up environments...")
            try:
                self.server_manager.setup_virtual_environments()
                self.root.after(0, lambda: self.update_status("Environments set up successfully"))
                self.root.after(0, self.check_environments)
            except Exception as e:
                logger.error(f"Environment setup failed: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Environment setup failed: {e}"
                ))
            finally:
                self.root.after(0, self.hide_progress)
        
        threading.Thread(target=setup_task, daemon=True).start()
    
    def check_environments(self):
        """Check the status of virtual environments."""
        status = self.server_manager.check_environment_status()
        self.env_status_var.set(status)
    
    def cleanup_all_servers(self):
        """Clean up all running servers."""
        try:
            self.server_manager.cleanup_all()
            self.diarization_server_btn.config(text="Start Diarization Server")
            self.transcription_server_btn.config(text="Start Transcription Server")
            self.diarization_status_var.set("Server: Stopped | Browser: Not opened")
            self.transcription_status_var.set("Server: Stopped | Browser: Not opened")
            self.update_status("All servers stopped")
            logger.info("All servers cleaned up")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            messagebox.showerror("Error", f"Cleanup failed: {e}")
    
    def clear_logs(self):
        """Clear the log display."""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def show_progress(self, message: str):
        """Show progress bar with message."""
        self.progress_bar.start(10)
        self.update_status(message)
    
    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.stop()
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_var.set(message)
    
    def exit_application_with_cleanup(self):
        """Exit application with complete cleanup including virtual environments."""
        result = messagebox.askyesnocancel(
            "Exit ALF", 
            "Do you want to exit and remove all virtual environments?\n\n"
            "This will:\n"
            "• Stop all running servers\n"
            "• Delete all virtual environments (.venvs directory)\n"
            "• Clean up temporary files\n"
            "• Close the application\n\n"
            "Click 'Yes' to exit with full cleanup\n"
            "Click 'No' to exit without removing environments\n"
            "Click 'Cancel' to stay in the application"
        )
        
        if result is True:  # Yes - exit with full cleanup
            self._perform_full_cleanup_and_exit()
        elif result is False:  # No - exit without removing environments
            self.on_closing()
    
    def _perform_full_cleanup_and_exit(self):
        """Perform full cleanup in a background thread and exit."""
        def cleanup_task():
            try:
                self.show_progress("Performing complete cleanup...")
                self.root.after(0, lambda: self.update_status("Stopping all servers..."))
                
                # Perform complete cleanup including virtual environments
                self.server_manager.cleanup_all_and_exit()
                
                # Also cleanup processed audio files
                try:
                    self.audio_preprocessor.cleanup_processed_files()
                except:
                    pass  # Don't fail if audio cleanup has issues
                
                self.root.after(0, lambda: self.update_status("Cleanup completed - exiting application"))
                logger.info("Full cleanup completed - application exiting")
                
                # Close the application
                self.root.after(1000, self.root.destroy)  # Small delay to show final message
                
            except Exception as e:
                logger.error(f"Error during full cleanup: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Cleanup Error", 
                    f"Some cleanup operations failed: {e}\n\nApplication will still exit."
                ))
                self.root.after(2000, self.root.destroy)  # Exit even if cleanup fails
            finally:
                self.root.after(0, self.hide_progress)
        
        threading.Thread(target=cleanup_task, daemon=True).start()
    
    def on_closing(self):
        """Handle application closing without virtual environment cleanup."""
        if messagebox.askokcancel("Quit", "Do you want to quit? This will stop all running servers."):
            self.cleanup_all_servers()
            self.root.destroy()
    
    def run(self):
        """Start the main application loop."""
        logger.info("Starting main application loop")
        self.check_environments()  # Initial environment check
        self.root.mainloop()