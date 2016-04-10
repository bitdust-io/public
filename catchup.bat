@echo off
SET srcpath=..\bitdust
SET tmppath=..\bitdust.tmp
SET curpath=%cd%
git pull
mkdir %tmppath%
cd "%srcpath%"
git checkout-index -a -f --prefix="%tmppath%//"
cd "%tmppath%"
rm -f .gitignore
rm -rf release/
rm -rf screenshots/
rm -rf scripts/
rm -rf tests/
rm -rf deploy/
cp -r * "%curpath%"
cd "%curpath%"
rm -rf "%tmppath%"
git add -u :/
git status
pause 
git commit -m "catch up development repo : %Date:~% at %Time:~0,8%"
git push origin
git push github