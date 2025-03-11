nowz = datetime.now()
czas = nowz.strftime("%m-%d-%Y %H.%M")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
SITE = "Breuninger"
phone_prefix = {
    "PL":"+48",
    "CZ":"+420",
    "SK":"+421",
    "ES":"+34",
    "FR":"+33",
    "IT":"+39",
    "NL":"+31",
    "DE":"+49",
    "CH":"+41",
    "AT":"+43",
    "BE":"+32"
}
def log(text, color,site):
    timestamp = datetime.today()
    message = f"{color}[{str(timestamp.time())}][{site}]{text}"
    message_log = f"[{str(timestamp.time())}][{site}]{text}"
    if site != None:
        with open(f"Logs/{czas}.txt", 'a', encoding='utf-8') as file:
            file.write(message_log + '\n')
    print(message)