import tkinter as tk
from tkinter import ttk
import clips
import tempfile
import os

# --- CLIPS Knowledge Base ---
# This string defines the rules for our expert system.
KNOWLEDGE_BASE = """
(deftemplate patient
   (slot fever (type SYMBOL) (default no))
   (slot cough (type SYMBOL) (default no))
   (slot loss-of-smell (type SYMBOL) (default no))
   (slot contact-with-patient (type SYMBOL) (default no))
)

(deftemplate result
   (slot message (type STRING))
)

(defrule rule-1-high-risk
   "Rule 1: High risk if patient has fever and loss of smell"
   (patient (fever yes) (loss-of-smell yes))
   =>
   (assert (result (message "Diagnosis: High Risk for COVID-19. Please get tested immediately and isolate.")))
)

(defrule rule-2-moderate-risk
   "Rule 2: Moderate risk if patient has fever, cough, and known contact"
   (patient (fever yes) (cough yes) (contact-with-patient yes))
   (not (result))
   =>
   (assert (result (message "Diagnosis: Moderate Risk for COVID-19. Monitor symptoms closely and consider testing.")))
)

(defrule rule-3-low-risk
   "Rule 3: Low risk default"
   (patient)
   (not (result))
   =>
   (assert (result (message "Diagnosis: Low Risk. Symptoms may be due to other causes. Monitor your health.")))
)
"""

class CovidExpertSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("COVID-19 Diagnosis Expert System")
        self.root.geometry("500x450")
        self.root.configure(bg="#0be2b3")

        # Initialize CLIPS environment
        self.env = clips.Environment()
        
        # --- NEW ROBUST METHOD TO LOAD RULES ---
        # We will write the rules to a temporary file and use .load()
        # This is more reliable than .build() which was causing errors.
        temp_file_path = None
        try:
            # Create a named temporary file
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.clp', encoding='utf-8') as temp_file:
                temp_file.write(KNOWLEDGE_BASE)
                temp_file_path = temp_file.name
            
            # Load the rules from the temporary file
            self.env.load(temp_file_path)

        except Exception as e:
            # Handle any error during file creation or loading
            print(f"FATAL ERROR: Failed to load CLIPS rules: {e}")
            # We'll show this in the UI as well
            self.result_var.set(f"FATAL ERROR: Failed to load rules: {e}")
            # Don't destroy root, so user can see the error
        finally:
            # Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        # --- End of new rule loading method ---

        # Style
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Helvetica", 12))
        self.style.configure("TCheckbutton", font=("Helvetica", 11))
        self.style.configure("TButton", font=("Helvetica", 12, "bold"))
        self.style.configure("Result.TLabel", font=("Helvetica", 12, "bold"))

        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        title_label = ttk.Label(main_frame, text="Please answer the following questions:", font=("Helvetica", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # --- UI Variables ---
        self.fever_var = tk.StringVar(value="no")
        self.cough_var = tk.StringVar(value="no")
        self.loss_of_smell_var = tk.StringVar(value="no")
        self.contact_var = tk.StringVar(value="no")
        self.result_var = tk.StringVar(value="Diagnosis will appear here.")

        # --- UI Widgets ---
        # Fever Checkbox
        cb_fever = ttk.Checkbutton(
            main_frame,
            text="Do you have a fever?",
            variable=self.fever_var,
            onvalue="yes",
            offvalue="no"
        )
        cb_fever.pack(anchor="w", pady=5)

        # Cough Checkbox
        cb_cough = ttk.Checkbutton(
            main_frame,
            text="Do you have a persistent cough?",
            variable=self.cough_var,
            onvalue="yes",
            offvalue="no"
        )
        cb_cough.pack(anchor="w", pady=5)

        # Loss of Smell Checkbox
        cb_smell = ttk.Checkbutton(
            main_frame,
            text="Have you lost your sense of taste or smell?",
            variable=self.loss_of_smell_var,
            onvalue="yes",
            offvalue="no"
        )
        cb_smell.pack(anchor="w", pady=5)

        # Contact Checkbox
        cb_contact = ttk.Checkbutton(
            main_frame,
            text="Have you been in close contact with a confirmed case?",
            variable=self.contact_var,
            onvalue="yes",
            offvalue="no"
        )
        cb_contact.pack(anchor="w", pady=5)

        # Diagnose Button
        diagnose_button = ttk.Button(
            main_frame,
            text="Get Diagnosis",
            command=self.run_diagnosis
        )
        diagnose_button.pack(pady=20)

        # Result Label
        result_label = ttk.Label(
            main_frame,
            textvariable=self.result_var,
            style="Result.TLabel",
            wraplength=400,
            justify=tk.CENTER
        )
        result_label.pack(pady=(10, 0))

    def run_diagnosis(self):
        # 1. Reset the CLIPS environment
        self.env.reset()

        # 2. Get values from the UI
        fever = self.fever_var.get()
        cough = self.cough_var.get()
        loss_of_smell = self.loss_of_smell_var.get()
        contact = self.contact_var.get()

        # 3. Assert the patient fact into the environment
        fact_string = f"(patient (fever {fever}) (cough {cough}) (loss-of-smell {loss_of_smell}) (contact-with-patient {contact}))"
        self.env.assert_string(fact_string)

        # 4. Run the expert system
        self.env.run()

        # 5. Find and display the. result
        result_found = False
        for fact in self.env.facts():
            if fact.template.name == 'result':
                # Get the message from the 'result' fact's 'message' slot
                self.result_var.set(fact['message'])
                result_found = True
                break
        
        if not result_found:
            # This is a fallback, though our rules should always provide one
            self.result_var.set("Could not determine diagnosis.")

def main():
    root = tk.Tk()
    app = CovidExpertSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()