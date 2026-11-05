import configparser

settings = configparser.ConfigParser(interpolation=None, strict=True)
settings.read_string("[export]\npattern = paid%complete\nretention_days = 47\n")
print("pattern", settings["export"]["pattern"])
print("retention", settings.getint("export", "retention_days"))

duplicate = configparser.ConfigParser(interpolation=None, strict=True)
try:
    duplicate.read_string("[export]\nRetention = 47\nretention = 73\n")
except configparser.DuplicateOptionError:
    print("case_duplicate_rejected", True)
