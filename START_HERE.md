# 🎯 START HERE - New Developer Onboarding

Welcome to the Algorithmic Trading Research Platform!

---

## 📋 Read These Files IN ORDER

### 1. **[PROJECT_STATE.md](PROJECT_STATE.md)** ⭐ **READ THIS FIRST**
Complete project overview including:
- What the project does
- Current implementation status
- Architecture explanation
- How to set up and run
- Known issues and limitations
- Everything needed to continue development

**Time**: 15-20 minutes

---

### 2. **[README.md](README.md)** 
Quick reference guide:
- Feature overview
- Architecture diagram
- Usage examples
- Built-in strategies

**Time**: 5-10 minutes

---

### 3. **[QUICKSTART.md](QUICKSTART.md)**
Step-by-step tutorial:
- Installation instructions
- First data ingestion
- First backtest
- Web interface walkthrough

**Time**: 20 minutes (hands-on)

---

## 🎓 Optional Deep Dives

### **[plan_now.md](plan_now.md)** - Phase 1 Plan
Detailed implementation plan for Phase 1 (COMPLETED).
Shows what was built and why.

### **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Phase 1 Report
Complete report of Phase 1 implementation with code examples and metrics.

### **[plan_future.md](plan_future.md)** - Phase 2 Roadmap
Future development plan including LLM integration and self-evolution.

### **[STRUCTURE.md](STRUCTURE.md)** - File Structure
Detailed breakdown of every file and directory.

---

## ⚡ Quick Setup (Copy-Paste)

```bash
# Windows PowerShell
cd d:\Git_repos\alg_trader
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py load_strategies
python manage.py runserver 9000

# Visit: http://127.0.0.1:9000/
```

---

## 🆘 Having Issues?

1. **Check [PROJECT_STATE.md](PROJECT_STATE.md) → Troubleshooting section**
2. **Verify Python version**: Python 3.8+ required
3. **Ensure virtual environment is activated**: `(venv)` in terminal prompt
4. **Database issues**: Delete `db.sqlite3`, run `python manage.py migrate`

---

## ✅ You're Ready When...

- [ ] You've read PROJECT_STATE.md
- [ ] You've completed QUICKSTART.md tutorial
- [ ] You can run the dev server
- [ ] You've successfully run a backtest
- [ ] You understand the 3-layer architecture (Strategy → Portfolio → Execution)

---

**Next**: Open [PROJECT_STATE.md](PROJECT_STATE.md) and start reading!
