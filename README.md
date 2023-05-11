# ✒️ Introduction

* A tool to read comment of a live video in Facabook
* Python 3.10
* Beta

# 🛠️ Installation

Create virtualenv and activate
```bash
> virtualenv venv
```
```bash
> venv/Scripts/activate
```
Install lib
```bash
> pip install -r requirements.txt
```
Configure in the file **config.json**
```json
{
    "page_id": "",
    "cookie": "",
    "time_sleep": 18,
    "name_chatbot": "Chị Google"
}
```
[Optional] To use FPT's text-to-speech, register at [FPT.ai](https://fpt.ai/tts). Add your api-key in the file **api_fpt.json**
```json
[
    "5KSdfgfdgFlpIưgDvk2ghco81zjjG7bw",
    "33Srmb7QlyEbtje7rrgerfbAue2VOcVm"
]
```
Run
```bash
> python program.py
```
# 📑 Documentations

* [Facebook Graph API](https://developers.facebook.com/docs/graph-api/overview)
* [FPT Text-to-speech API](https://docs.fpt.ai/docs/en/speech/api/text-to-speech)