import logging

class Logs:
    def __init__(self, pathfile="logging.log"):
        logging.basicConfig(filemode='a',
                    filename=f"{pathfile}",
                    encoding="utf-8",
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
        self.warning_logs(f"Log file :[{pathfile}] has been saved!")

    def error_logs(self, error_msg):
        logging.error(error_msg)
    def warning_logs(self, warning_msg):
        logging.warning(warning_msg)

    def critical_logs(self, critical_msg):
        logging.critical(critical_msg)

    def info_logs(self, info_msg):
        logging.info(info_msg)


