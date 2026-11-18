# Lista original
tickers = """
TOST   RUN   CVNA   PCG   GILD   FITB   RF   SO   KDP   HST   PPL   KR   MIR   DX   CNP   AGNC   GOOG   GOOGL   V   SHOP   PG   GPK   META   EXC   KVUE   RTX   KEY   HBAN   AAPL   APH   PM   D   SATS   QXO   WFC   NLY   BAC   HD   MS   USB   PYPL   UMAC   SCHW   RKT   XE   JPM   IR   GE   CELH   KRMN   BKD   IBN   NU   ALHC   SOFI   CLSK   BE   RIOT   HDB   HIMS   CRH   B   XYZ   COF   LUV   NEM   EQX   JHX   KGC   RELY   CCL   AAL   FCEL   CPNG   PEB   CIFR   AFRM   RBLX   BBWI   MRNA   ALM   MGNI   AG   CRWV   ELF   NBIS   LION   AMKR   SVM  
"""

# Convertir espacios y saltos de línea a comas
resultado = ",".join(tickers.split())

# Guardar en archivo TXT
with open("./strategies/vcp_scanner/input/tickers.txt", "w", encoding="utf-8") as f:
    f.write(resultado)

print("Archivo creado correctamente.")

