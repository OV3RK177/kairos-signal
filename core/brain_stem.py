import threading
import os

def launch_neural(): os.system("python3 core/neural_link.py")
def launch_account(): os.system("python3 core/accountant.py")

if __name__ == "__main__":
    t1 = threading.Thread(target=launch_neural)
    t2 = threading.Thread(target=launch_account)
    t1.start(); t2.start()
    t1.join(); t2.join()
