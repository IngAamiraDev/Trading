# Lista original
tickers = """
 CASY   ATEX   TGTX   CXW   ZVRA   CHEF   LQDA   CRS   GEO   SNEX   PDFS   ENVA   RSI   VPG   AMAT   SXT   BTSG   MOG-A   PKE   DAVE   UFCS   ATRO   LGND   ELA   VSXY   LRCX   VIRT   VVX   LPG   DAKT   UAL   LUV   SNDK   INCY   SEZL   MCB   COCO   HWM   SPHR   NWPX   TILE   SHC   SFST   CCNE   PGC   EXTR   TCMD   MKSI   KRYS   PSTL   PRLB   WST   CARE   KLIC   MNST   LC   RS   LLY   AMKR   RDVT   ALAB   ROST   NGS   CTS   ARMK   MLI   CMC   CW   MCY   TTMI   PLXS   STLD   JBL   ADEA   KALU   OOMA   MU   SNX   ECPG   SEI   NUE   PHIN   ARW   KEYS   ORN   SSSS   IESC   FCFS   MTSI   MS   VICR   HLIO   TXN   FTNT   MAMA   MCHP   FIX   ADI   CGNX   BLLN   ROKU   FCX   DY   PWR   DIOD   VCYT   WCC   ANET   MYRG   LINC   SCCO   STX   TER   CSCO   AMD   VSH   GLW   HCC   IONQ   SANM   TWLO   HPE   INOD   COHR   FSLR   MRAM   STRL 
"""

# Convertir espacios y saltos de línea a comas
resultado = ",".join(tickers.split())

# Guardar en archivo TXT
with open("./strategies/vcp_scanner/input/tickers.txt", "w", encoding="utf-8") as f:
    f.write(resultado)

print("Archivo creado correctamente.")

