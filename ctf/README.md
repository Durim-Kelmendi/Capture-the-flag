## Getting started

Clone this repo and then remove the `.git` folder:
```
git clone https://gitlab.ida.liu.se/tdde25/ctf
cd ctf
rm -rf .git
```
Then add your own git folder per the instructions on the TDDE25 git tutorial.


We also need to add the required libraries pymunk and pygame (if you're doing this in your own computer, then just pip install as usual):
```
pip3 install --upgrade --user setuptools pip
cd ~/.local/bin
./pip3 install --user pymunk
./pip3 install --user pygame
```
Now, all these local installations will end up in `~/.local/lib/python3.4/site-packages`, so we'll need to add it to our `PYTHONPATH`. 
We'll do this by modyfying the bash file that gets run every time we open up a new terminal (`~/.bashrc`). Add this line to your `~/.bashrc` file:
```
export PYTHONPATH = "~/.local/lib/python3.4/site-packages:${PYTHONPATH}"
```

If you restart your terminal and run this, then the pygame version should be 1.9.4 or higher:
```python
python3
>>> import pygame
>>> pygame.__version__
'1.9.4'
```


Next go to our [wiki](https://gitlab.ida.liu.se/tdde25/ctf/wikis/home) and get started on the tutorials.