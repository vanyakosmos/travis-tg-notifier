# Travis CI telegram notifications

[![Build Status](https://travis-ci.org/vanyakosmos/travis-tg-notifier.svg?branch=master)](https://travis-ci.org/vanyakosmos/travis-tg-notifier)
[![Coverage](https://codecov.io/gh/vanyakosmos/travis-tg-notifier/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/travis-tg-notifier)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/vanyakosmos/travis-tg-notifier/tree/master)

## Usage

- go to [https://travis-tg.herokuapps.com](https://travis-tg.herokuapps.com)
- login via telegram
- use generated url as webhook in `.travis.yml`:

```
notifications:
  webhooks:
    - https://travis-tg.herokuapps.com/u/1234
```

- after each build you will receive notification from [@TravisCINotifierBot](https://t.me/TravisCINotifierBot).


## Usage without telegram authentication or in groups

- initiate dialog with [@TravisCINotifierBot](https://t.me/TravisCINotifierBot) or add it to the chat.
- find out telegram id of group chat (or yours). Try [@JsonDumpBot](https://t.me/JsonDumpBot) 
- add `/force` to the webhook url

```
notifications:
  webhooks:
    - https://travis-tg.herokuapps.com/u/TELEGRAM_ID/force
```
