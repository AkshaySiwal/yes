```
# Install pyenv via Homebrew
brew install pyenv

# Add to your shell configuration (~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell configuration
source ~/.zshrc

# Set Python 3.13 as your global default
pyenv global 3.13

```




```
# Install pyenv-virtualenv plugin
brew install pyenv-virtualenv

# Add to shell configuration
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
source ~/.zshrc

# Create and activate virtual environments
pyenv virtualenv 3.13 my-project
pyenv activate my-project
```
