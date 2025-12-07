#  HACK_SAP – Rotables Simulation Project

This project simulates **airline rotables logistics** and provides:

*  A **console application** (`rotables.main`)
*  A **frontend** for visualizing simulation data
*  A **backend** to run simulations

---

##  Running the Console Application

From the **root folder** `HACK_SAP/`, run:

```bash
python3 -m rotables.main
```

> On Windows, if `python3` is not available, you can also use:
>
> ```bash
> python -m rotables.main
> ```

The output will be printed in the terminal and saved in:

```
D:\HackITAll\copy\HACK_SAP\rotables\logs\debug_output.txt
```

---

## 🌐 Frontend and Backend

The project also includes a **frontend** and **backend**.
For setup instructions, see:

```
D:\HackITAll\copy\HACK_SAP\frontend\setup.txt
```

Follow the instructions in that file to:

1. Start the **backend** server
2. Run the **frontend** for a graphical dashboard
3. Connect the frontend to the backend to run simulations

---

## 📂 Project Structure

```
HACK_SAP/
│
├─ rotables/             # Core simulation logic
├─ backend/              # FastAPI backend
└─ frontend/             # React frontend
```

---

## ⚙️ Requirements

* Python 3.11+
* Node.js and npm/yarn (for frontend)
* FastAPI and Uvicorn (backend dependencies)
* Recharts (frontend chart library)

---


