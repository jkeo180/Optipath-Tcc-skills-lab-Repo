Why am I building this?
Optipath is a medical consulting company, Optipath is concerned with the mismatch between insurance providers and consumers and hopes to address this issue by providing data about local areas and their needs.

What exactly do I want this project to do?
I am using an ai agent along with pandas data to parse through data and using to select the correct parameters for area

How does this help others?
This project provides a clean, well-documented instructions connecting developers and users on how the project works

How does this work
I am designing this project with accuracy and easy of use for it's consumers

Core Logic
Unlike a general chatbot, this project uses a structured **Agent-to-Data** pipeline:
1. Input: User asks about a local area's health needs.
2. Agent (`agent.py`): Parses the intent and selects the right parameters.
3. Data (`analyze_data.py`): Executes high-speed Pandas filtering on local datasets.
4. medical_access: Executes specifically pandas filtering of medical data such as doctor location from the CDC
4. **UI:** UI is the front end.

Project structure
optipath/
├── README.md
├── LICENSE
├── .gitignore
├── ui.py          ← Streamlit UI
├── agent.py        ← LangChain agent
├── analyze_data.py         ← Pandas data functions
├── requirements.txt 


Tech Stack
- UI: Streamlit
- Orchestration: LangChain
- Data Handling: Pandas

How to contribute
contact me through GitHub I love collaborating and then clone
*https://github.com/jkeo180/Optipath-Tcc-skills-lab-Repo/tree/main*
