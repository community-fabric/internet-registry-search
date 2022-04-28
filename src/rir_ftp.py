import ftplib


def arin():
    ftp = ftplib.FTP("ftp.arin.net")
    ftp.login("anonymous", "ftplib-example-1")
    ftp.cwd("/pub/stats/arin/")
    with open('rir/arin.txt', "wb") as file:
        ftp.retrbinary(f"RETR delegated-arin-extended-latest", file.write)


def apnic():
    ftp = ftplib.FTP("ftp.apnic.net")
    ftp.login("anonymous", "ftplib-example-1")
    ftp.cwd("/public/stats/apnic/")
    with open('rir/apnic.txt', "wb") as file:
        ftp.retrbinary(f"RETR delegated-apnic-extended-latest", file.write)


def afrinic():
    ftp = ftplib.FTP("ftp.afrinic.net")
    ftp.login("anonymous", "ftplib-example-1")
    ftp.cwd("stats/afrinic/")
    with open('rir/afrinic.txt', "wb") as file:
        ftp.retrbinary(f"RETR delegated-afrinic-extended-latest", file.write)


def lacnic():
    ftp = ftplib.FTP("ftp.lacnic.net")
    ftp.login("anonymous", "ftplib-example-1")
    ftp.cwd("pub/stats/lacnic/")
    with open('rir/lacnic.txt', "wb") as file:
        ftp.retrbinary(f"RETR delegated-lacnic-extended-latest", file.write)


def ripe():
    ftp = ftplib.FTP("ftp.ripe.net")
    ftp.login("anonymous", "ftplib-example-1")
    ftp.cwd("pub/stats/ripencc/")
    with open('rir/ripe.txt', "wb") as file:
        ftp.retrbinary(f"RETR delegated-ripencc-extended-latest", file.write)


def download_all():
    apnic()
    afrinic()
    arin()
    lacnic()
    ripe()
