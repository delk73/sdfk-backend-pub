git checkout dce-dev
git pull
git branch | grep 'codex' | xargs git branch -D
./test.sh
