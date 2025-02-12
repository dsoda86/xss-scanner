import scanner

target_url = "http://127.0.0.1/DVWA" #localhost
links_to_ignore = ["http://127.0.0.1/DVWA/logout.php"]

data_dict = {"username" : "admin", "password" : "password" , "login" : "submit"}

dvwa_scanner = scanner.Scanner(target_url, links_to_ignore)
dvwa_scanner.session.post("http://127.0.0.1/DVWA/login.php", data=data_dict)

dvwa_scanner.crawl()
dvwa_scanner.run_scanner

