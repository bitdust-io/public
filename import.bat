@echo off
SET tmppath=%1.tmp
SET curpath=%cd%
git pull
cd %1
mkdir %tmppath%
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
git status
