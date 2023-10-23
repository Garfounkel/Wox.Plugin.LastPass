import re
import time
import subprocess
from dataclasses import dataclass
from tkinter import Tk
from wox import Wox


@dataclass
class LastPassEntry:
    lp_id: str
    action_id: str
    group: str
    name: str


class LastPassSearch(Wox):
    def query(self, arg):
        def result(lp_entry: LastPassEntry):
            if lp_entry.action_id == "default":
                return {
                    "Title": lp_entry.name,
                    "SubTitle": lp_entry.group,
                    "IcoPath": "Images/app.png",
                    "ContextData": [lp_entry.lp_id],
                    "JsonRPCAction": {
                        "method": "copy_password",
                        "parameters": [lp_entry.lp_id],
                    },
                }
            if lp_entry.action_id == "sign_in":
                return {
                    "Title": lp_entry.name,
                    "SubTitle": lp_entry.group,
                    "IcoPath": "Images/app.png",
                    "JsonRPCAction": {
                        "method": "sign_in",
                        "parameters": [lp_entry.lp_id],
                    },
                }

        search_term = arg.lower()

        def search_criteria(name: str, group: str):
            name = name.lower()
            group = group.lower()
            name_matches = [sub for sub in search_term.split() if sub in name]
            group_matches = [sub for sub in search_term.split() if sub in group]
            return (
                len(name_matches) == len(search_term.split())
                or len(group_matches) == len(search_term.split())
                or search_term in name
                or search_term in group
            )

        ls_process = subprocess.Popen(
            ["powershell.exe", 'wsl --exec bash -c "/usr/bin/lpass ls --sync=no --color=never --format=\'%aN [id: %ai] %au\'"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        output = ls_process.stdout.readlines()
        regex_pattern = re.compile(r"(.*)\/(.*)\s\[id:\s(\d+)\] (.*)")
        formatted = []
        for line in output:
            entry_str = line.decode("utf-8")
            matches = regex_pattern.match(entry_str)
            if matches:
                group, name, acc_id, username = matches.group(1), matches.group(2), matches.group(3), matches.group(4)
                lp_entry = LastPassEntry(
                    lp_id=acc_id,
                    action_id="default",
                    group=f"{username}",
                    name=f"{name}",
                )
                formatted.append(lp_entry)
            else:
                lp_entry = LastPassEntry(
                    lp_id=search_term,
                    action_id="sign_in",
                    group=f"Using the command: wsl --exec bash -c '/usr/bin/lpass login --trust USERNAME'",
                    name="Sign in to LastPass in the PowerShell",
                )
                formatted.append(lp_entry)
        return [
            result(entry)
            for entry in formatted
            if search_criteria(entry.name, entry.group) or entry.action_id == "sign_in"
        ]

    def _copy_text_to_clipboard(self, text: str):
        tk = Tk()
        tk.withdraw()
        tk.clipboard_clear()
        tk.clipboard_append(text)
        tk.update()
        time.sleep(0.2)
        tk.update()
        tk.destroy()

    def copy_password(self, lp_id: str):
        password_process = subprocess.Popen(
            ["powershell.exe", f"wsl --exec bash -c '/usr/bin/lpass show --sync=no --password {lp_id}'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        output = password_process.stdout.readlines()
        password = output[0].decode("utf-8")
        self._copy_text_to_clipboard(password)

    def copy_username(self, lp_id: str):
        password_process = subprocess.Popen(
            ["powershell.exe", f"wsl --exec bash -c '/usr/bin/lpass show --sync=no --username {lp_id}'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        output = password_process.stdout.readlines()
        username = output[0].decode("utf-8")
        self._copy_text_to_clipboard(username)

    def sign_in(self, username: str):
        login_process = subprocess.Popen(["powershell.exe"])
        # How to fill in the username into the powershell process using stdin?

    def context_menu(self, lp_id: str):
        """Function that is called when context menu is triggered (shift-enter).
        ctx_data is the value set in from ContextData from query.
        """
        results = [
            {
                "Title": "Copy password",
                "JsonRPCAction": {
                    "method": "copy_password",
                    "parameters": lp_id,
                },
            },
            {
                "Title": "Copy username",
                "JsonRPCAction": {
                    "method": "copy_username",
                    "parameters": lp_id,
                },
            },
        ]
        return results


if __name__ == "__main__":
    LastPassSearch()
