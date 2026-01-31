# Reservations_System


## Installing and running the project
1. Create virtual environment venv:
```
py -m venv venv
```

2. Activate virtual environment from cmd:
```
.\venv\Scripts\activate
```

3. Install requirements:
```
pip install -r requirements.txt
```

4. Create a `.env` file like this and replace with a valid key :
```
OPENAI_API_KEY=sk-....
```


5. Run backend:
```
uvicorn backend.app:app --reload --port 8000
```

6. Run frontend: (streamlit UI):
```
streamlit run frontend/streamlit_app.py
```




### Setup
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt

### Run API
uvicorn app:app --reload

### Use CLI (in another terminal)
python cli.py create-user alice
python cli.py create-user admin --admin
python cli.py list-users
python cli.py add-room 2 "Sala A1" 20
python cli.py add-room 2 "Sala B2" 40

python cli.py list-rooms --mincap 10

python cli.py reserve 1 1 2026-01-21 2026-01-23
python cli.py availability 2026-01-21 2026-01-21 --mincap 10
python cli.py my-reservations 1
python cli.py cancel 1 1
python cli.py occupancy 2026-01-21
