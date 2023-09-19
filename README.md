<div style="text-align: center">
  <img src="img/hammer_py.png">
</div>

# HammerPy

HammerPy is a game where users guess the price of artwork available on auction websites. The name comes from the term "hammer price", which refers to the final selling price of a work. Asking prices are used instead for art that is still available for sale.

Currently the game retrieves artwork from the [Artsy](https://www.artsy.net/) art exchange, though other sources and popular auction sites will be added in the future.

## Setup and Installation

HammerPy requires >= Python 3.8

Dependencies:
- requests
- urllib3
- Pillow

```
pip install -r requirements.txt
python hammer.py
```

## Quickstart

The game is fairly straightforward because it's open ended - enter the price you think is closest to the worth of the displayed artwork. You cannot go backwards after submitting a guess. Once all guesses have been turned in, the game takes you to the results screen where you can view metadata for the artwork including the real price, what the acceptable range of guesses was, and whether you were correct.

All prices are in USD - any works that have prices in foreign currencies are converted to USD for the game.

There are 3 difficulty levels:
- **Easy**: +/- 25% from actual price
- **Medium**: +/- 15% from actual price
- **Hard**: +/- 5% from actual price

Fetching the art might take a while as the bottleneck here is network speed. If the number of requested works is >= 5, then a `time.sleep` call for 5 seconds is added to avoid spamming the service with requests

HammerPy downloads the images of the art to your computer temporarily for the lifespan of the game. On the results screen, you can decide if you'd like to keep the images for any of the art you like. By default, this is set to `False`, and any artwork you do not explicitly mark as wanting to keep is removed from your system

## Screenshots


