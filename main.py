import schedule
import time
import parser
import ps_parser2
import xparser

schedule.every().day.at('12:00').do(xparser.parse)
schedule.every().day.at('12:00').do(ps_parser2.parsing)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
