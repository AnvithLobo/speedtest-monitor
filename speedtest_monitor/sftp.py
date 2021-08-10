import paramiko

from pathlib import Path

db_path = (Path(__file__).parent / 'secrets' / 'speedtest_log.sqlite').absolute()
KEY_PATH = (Path(__file__).parent / 'secrets' / 'speedtest-monitor-key').absolute()

# Open a transport
# ToDo: Parse from config   (db_path, KEY_PATH, host, port, username, remote_path)

host, port = "IP", 2121

# Auth
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, port=port, username='username',
               key_filename=str(KEY_PATH))


# Go!
sftp = paramiko.SFTPClient.from_transport(client.get_transport())

# Upload
# ToDo: add a config method to get paths
filepath = "remote_path"
localpath = str(db_path)
sftp.put(localpath, filepath)

# Close
if sftp:
    sftp.close()

client.close()
