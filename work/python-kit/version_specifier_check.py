from packaging.specifiers import SpecifierSet
from packaging.version import Version

accepted = SpecifierSet(">=2.4,<3")
for candidate in ("2.4", "2.5rc1", "3.0"):
    print(candidate, accepted.contains(Version(candidate), prereleases=False))
