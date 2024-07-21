# YumeTravel

> A simplistic llama3-based AI recommendation chatbot for travelling lovers

**Note: In no way, the code is cleaned as this was developed for a 48-hour hackathon**

The backend is currently running on https://yumequest.htetaung.com/api.

## How to run?
1. Create a python virtual environment
```
python3 -m venv .venv
```
2. Install all the necessary packages
```
pip3 install -r requirements.txt
```
3. Check out sample.env and set up .env variables accordingly
```
TOGETHER_API_KEY=
AMADEUS_API_URL=https://test.api.amadeus.com/v2
AMADEUS_API_KEY=
AMADEUS_API_SECRET=
```

3. Run the server!
```
fastapi run src/main.app --host {{Your IP}} --port {{Your Port}}
```