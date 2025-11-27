

#2025-11-17-01

#to start manually on linux:
#pkill mpv -e ; pkill python -e; python mpvs.py
#on windows: 
#taskkill", "/F", "/IM", "mpv.exe"]
#taskkill", "/F", "/IM", "python.exe"]
#python mpvs.py

import os, json, socket
import socket as S_socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
import subprocess
import time
import platform

MPV_SOCKET = "/tmp/mpvsocket"
HOST = "0.0.0.0"
PORT = 8080
START_PATH = '/mnt/wd1TB/media/series/'
#or use current dir:
#START_PATH = os.getcwd()

python_win="python.exe"
python_linux="python"
mpv_win="mpv.exe"
mpv_linux="mpv"

def fn_terminate_python():
	system = platform.system()
	if system == "Windows":
		# /F: Force kill, /IM: Image name
		command = ["taskkill", "/F", "/IM", python_win]
		subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	elif system in ["Linux", "Darwin"]: # Darwin is macOS
		command = ["pkill", "-e", python_linux]
		subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def fn_terminate_mpv():
	system = platform.system()
	if system == "Windows":
		# /F: Force kill, /IM: Image name
		command = ["taskkill", "/F", "/IM", mpv_win]
		subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

	elif system in ["Linux", "Darwin"]: # Darwin is macOS
		command = ["pkill", "-e", mpv_linux]
		subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



fn_terminate_mpv()

# ---------------- MPV IPC -----------------
def mpv_cmd(cmd):
	msg = json.dumps({"command": cmd})
	s = S_socket.socket(S_socket.AF_UNIX, S_socket.SOCK_STREAM)
	try:
		s.connect(MPV_SOCKET)
		s.send((msg + "\n").encode())
	except (FileNotFoundError, ConnectionRefusedError):
		pass
	finally:
		s.close()

def mpv_get(prop):
	msg = json.dumps({"command": ["get_property", prop]})
	s = S_socket.socket(S_socket.AF_UNIX, S_socket.SOCK_STREAM)
	try:
		s.connect(MPV_SOCKET)
		s.send((msg + "\n").encode())
		data = s.recv(4096).decode()
		return json.loads(data).get("data")
	except (FileNotFoundError, ConnectionRefusedError):
		return None
	except:
		return None
	finally:
		s.close()

def is_mpv_socket_active():
	"""Checks if the MPV socket file exists and is connectable."""
	if not os.path.exists(MPV_SOCKET):
		return False
	
	s = S_socket.socket(S_socket.AF_UNIX, S_socket.SOCK_STREAM)
	s.setblocking(0)
	try:
		s.connect((MPV_SOCKET,))
		s.close()
		return True
	except (BlockingIOError, ConnectionRefusedError, FileNotFoundError):
		return False
	except Exception:
		return False
	finally:
		try:
			s.close()
		except:
			pass

def start_mpv_if_needed():
	"""Checks for the socket and starts MPV in the background if necessary."""
	if is_mpv_socket_active():
		print("[OK] MPV socket is already active.")
		return True

	print("[WARNING] MPV socket not found. Attempting to start MPV...")
	cmd = ["mpv", f"--input-ipc-server={MPV_SOCKET}", "--idle", "--no-terminal"]
	
	try:
		subprocess.Popen(
			cmd, 
			stdout=subprocess.DEVNULL, 
			stderr=subprocess.DEVNULL, 
			start_new_session=True
		)
		print("[SUCCESS] MPV started successfully in the background.")
		time.sleep(1) # Give MPV a moment to create the socket
		
		if is_mpv_socket_active():
			print("[OK] MPV socket confirmed active after startup.")
			return True
		else:
			print("[WARNING] MPV started, but socket not yet confirmed active. Proceeding...")
			return True
			
	except FileNotFoundError:
		print("[ERROR] MPV executable not found. Please ensure 'mpv' is installed and in your PATH.")
		return False
	except Exception as e:
		print(f"[ERROR] starting MPV: {e}")
		return False



# Updated get_offset_file function
def get_offset_file(current_path, offset):
	"""
	Calculates the file path at a given offset and the filename without extension.
	"""
	current_dir = os.path.dirname(current_path)
	current_filename = os.path.basename(current_path)
	
	if not os.path.isdir(current_dir):
		return None, None  # Return None for both path and name

	try:
		items = os.listdir(current_dir)
		files = sorted(
			[f for f in items if os.path.isfile(os.path.join(current_dir, f))],
			key=str.lower
		)
		
		try:
			current_index = files.index(current_filename)
		except ValueError:
			return None, None

		target_index = current_index + offset
		
		if 0 <= target_index < len(files):
			target_filename = files[target_index]
			target_path = os.path.join(current_dir, target_filename)
			
			# Use os.path.splitext to get the name without the extension
			name_without_ext = os.path.splitext(target_filename)[0]
			
			return target_path, name_without_ext  # Return both path and name
		else:
			return None, None
			
	except Exception:
		return None, None




# -------------- HTML PAGE ------------------
HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
<title>MPV Remote</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: sans-serif; padding: 10px; max-width: 700px; margin: auto; background: #111; color: #eee; }}
button {{ padding: 12px; margin: 3px; font-size: 16px; width: 100px; }}
#files div {{ padding: 8px; border-bottom: 1px solid #444; cursor: pointer; }}
#files div:hover {{ background: #222; }}
#up {{ padding: 8px; background: #222; margin-bottom: 10px; width: 100%; text-align: right; cursor: pointer; }}
input[type=range] {{ width: 100%; }}
</style>
</head>
<body>

<h2>MPV Remote</h2>
<button id="playBtn" onclick="togglePlay()">||</button>
<button onclick="seek(-10)">&lt;&lt;</button>
<button onclick="seek(10)">&gt;&gt;</button>
<br>
<button onclick="toggleFull()">|-[&nbsp;&nbsp;]-|</button>
<button onclick="volDown()">V-</button>
<button onclick="volUp()">V+</button>
<br>
<button onclick="cycleTrack('sub')">S</button>
<button onclick="send(['load-utils/load-prev']); resetProgressBarrAndText()">|&lt;</button>
<button onclick="send(['load-utils/load-next']); resetProgressBarrAndText()">&gt;|</button>
<br>
<button onclick="cycleTrack('audio')">A</button>
<button onclick="playlistPrev()">[=]&lt;</button>
<button onclick="playlistNext()">&gt;[=]</button>

<br><br>

<b>Progress: <span id="progress-label"></span></b>
<input id="seek" type="range" min="0" max="100" value="0" oninput="doSeek(this.value)">

<hr>

<p> <b>Volume: <span id="volume-label">100</span>%<b></p> 
<input type="range" id="volume-slider" min="0" max="130" value="100" oninput="setVolume(this.value)">


<hr>

<h3>File Browser</h3>
<p><b>Path:</b> <span id="path">{START_PATH}</span></p>
<span id="up" onclick="goUp()" style="display:block; width:100%; text-align:center; background:#222; padding:8px; cursor:pointer;">^^Up</span>
<div id="files"></div>

<script>
let current = "{START_PATH}";
let playingPaused = false;

function send(arr) {{
	fetch("/cmd?c=" + encodeURIComponent(JSON.stringify(arr)));
}}

function togglePlay(){{
	playingPaused = !playingPaused;
	send(["set_property","pause",playingPaused]);

	// Update button label
	const btn = document.getElementById("playBtn");
	btn.textContent = playingPaused ? "|>" : "||";
}}


function seek(sec){{
	send(["seek",sec,"relative"]);
	fetch("/status").then(r=>r.json()).then(s=>{{
		if(s.percent!==undefined && s.duration!==undefined){{
			// Update the progress bar slider value
			document.getElementById("seek").value = s.percent; 
			// Also update the OSD text for visual feedback
			osdPos(s.percent,s.duration);
		}}
	}});
}}


function resetProgressBarrAndText() {{
	document.getElementById("progress-label").textContent = "";
	document.getElementById("seek").value = 0;
	document.getElementById("progress-label").textContent = "";
}}


function volUp() {{
	send(["add", "volume", 5]);
	fetch("/status").then(r => r.json()).then(s => {{
		osdText("Volume: " + Math.round(s.volume) + "%");
		document.getElementById("volume-slider").value = s.volume;
		document.getElementById("volume-label").textContent = Math.round(s.volume);
	}});
}}

function volDown() {{
	send(["add", "volume", -5]);
	fetch("/status").then(r => r.json()).then(s => {{
		osdText("Volume: " + Math.round(s.volume) + "%");
		document.getElementById("volume-slider").value = s.volume;
		document.getElementById("volume-label").textContent = Math.round(s.volume);
	}});
}}

function setVolume(volume) {{
	volume = Math.min(130, Math.max(0, volume)); // Make sure volume stays between 0 and 130
	send(["set_property", "volume", volume]);
	fetch("/status").then(r => r.json()).then(s => {{
		osdText("Volume: " + volume + "%");
		document.getElementById("volume-label").textContent = volume;
	}});
}}

function doSeek(p){{
	send(["set_property","percent-pos",Number(p)]);
	fetch("/status").then(r=>r.json()).then(s=>{{
		if(s.percent!==undefined && s.duration!==undefined){{
			osdPos(s.percent,s.duration);
		}}
	}});
}}

function toggleFull(){{ send(["cycle","fullscreen"]); osdText("Toggle Fullscreen"); }}

function osdText(text){{
	send(["show_text", text, "1000"]);
}}

function osdPos(percent,duration){{
	let totalSec = duration || 0;
	let curSec = percent/100*totalSec;
	function fmt(t){{ let h=Math.floor(t/3600); let m=Math.floor((t%3600)/60); let s=Math.floor(t%60); return (h>0?h+":":"")+String(m).padStart(2,'0')+":"+String(s).padStart(2,'0'); }}
	let txt = fmt(curSec)+"/"+fmt(totalSec)+" "+Math.round(percent)+"%";
	osdText(txt);
	document.getElementById("progress-label").textContent = txt;
}}


function list(path){{
	current = path;
	document.getElementById("path").textContent = path;
	document.getElementById("seek").value = 0;
	fetch("/list?path=" + encodeURIComponent(path))
	.then(r => r.json())
	.then(items => {{
		let div = document.getElementById("files");
		div.innerHTML = "";
		items.forEach(name => {{
			let row = document.createElement("div");
			row.textContent = name;
			row.onclick = () => {{
				let full = path + (path.endsWith("/") ? "" : "/") + name;
				fetch("/isfile?path=" + encodeURIComponent(full))
				.then(r => r.json())
				.then(res => {{
					if(res.isFile){{
						send(["loadfile", full]);
						send(["set_property","pause",false]);
						send(["set_property","fullscreen",true]);
						resetProgressBarrAndText();
						let fileName = name.substring(0, name.lastIndexOf('.')) || name;
						if (fileName.length > 50) {{
							fileName = fileName.substring(0, 50) + '...';
						}}
						osdText(fileName);
					}} else {{
						list(full);
					}}
				}});
			}};
			div.appendChild(row);
		}});
	}});
}}



function goUp(){{
	if(current==="/") return;
	let parts=current.split("/").filter(x=>x);
	parts.pop();
	let newPath="/"+parts.join("/")+"/";
	list(newPath);
}}



function cycleTrack(type) {{
	// 1. Send the cycle command to MPV
	send(['cycle', type]);
	
	// 2. Wait slightly for MPV to complete the cycle and update its properties
	setTimeout(() => {{
		// 3. Fetch the updated track status from the Python server
		fetch("/track_status")
		.then(r => r.json())
		.then(data => {{
			// 4. Display the detailed, current track info on OSD
			if (type === 'audio') {{
				osdText(data.audio);
			}} else {{
				osdText(data.sub);
			}}
		}});
	}}, 200); // 200ms delay to ensure MPV updates properties after cycle
}}


function playlistPrev() {{
	fetch("/playlist_skip?dir=prev")
	.then(r=>r.json())
	.then(d=>{{
		osdText(d.name);
	}});
}}

function playlistNext() {{
	fetch("/playlist_skip?dir=next")
	.then(r=>r.json())
	.then(d=>{{
		osdText(d.name);
	}});
}}



window.onload=()=>{{ list(current); }};
</script>

</body>
</html>
"""

# -------------- HTTP HANDLER ----------------
class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path=="/":
			self.send_html(HTML_PAGE)

# In your Python script, add or ensure the 'time' import is present:
# import time # <--- Make sure this is at the top of your script

# Inside the Handler class, modify do_GET:

# ... (omitted existing elif blocks) ...

		elif self.path.startswith("/cmd?c="):
			cmd = json.loads(unquote(self.path.split("=",1)[1]))
			
			if cmd and len(cmd) > 0 and cmd[0] in ["load-utils/load-prev", "load-utils/load-next"]:
				
				offset = -1 if cmd[0] == "load-utils/load-prev" else 1
				
				current_file = mpv_get("path")
				if current_file:
					target_path, target_name = get_offset_file(current_file, offset)
					
					if target_path:
						if len(target_name) > 50:
							# Truncate and append '...'
							target_name = target_name[:50] + '...'

						# 1. Load the new file immediately
						mpv_cmd(["loadfile", target_path])
						#mpv_cmd(["set_property", "percent-pos", 0])
						
						# 2. WAIT briefly for MPV's default OSD to fade
						time.sleep(0.1) # 100 milliseconds delay
						
						# 3. Send custom OSD text using the clean name
						direction = "Prev" if offset == -1 else "Next"
						# Set OSD to last for 2000 milliseconds (2 seconds)
						mpv_cmd(["show_text", f"{direction}: {target_name}", "2000"]) 

					else:
						# If no target, show a message
						direction = "Previous" if offset == -1 else "Next"
						mpv_cmd(["show_text", f"End of folder reached for {direction}", "1000"])
						
					self.send_text("ok (custom skip)")
					return


			# If not a custom skip command, execute the original command
			mpv_cmd(cmd)
			self.send_text("ok")

			
			
		#cycle audio and subtitle
		elif self.path.startswith("/track_status"):
			# Fetch the current active IDs and Languages
			aid = mpv_get("aid")
			sid = mpv_get("sid")
			#print(aid, sid)
			# --- Fetch alang and slang (can be string or None) ---
			
			alang = ""
			slang = ""
			#fetch alang, slang? they could be None.
			
			total_audio = 0
			total_sub = 0
			# --- END Fetch ---
			
			track_list = mpv_get("track-list")
			#print("TRACK LIST", track_list)
			if track_list:
				for track in track_list:
					track_id = track.get("id")
					track_type = track.get("type")
					
					if track_type == "audio":
						total_audio += 1
						# Found the active internal audio track
						if track_id == aid:
							alang = track.get("lang") or track.get("title") or f"Track ID {aid}"
						
					elif track_type == "sub":
						total_sub += 1
						# Found the active internal subtitle track
						if track_id == sid:
							slang = track.get("lang") or track.get("title") or f"Track ID {sid}"						

			
			audio_info = f"Audio: {alang}({aid}/{total_audio})"
			subtitle_info = f"Subtitles: {slang}({sid}/{total_sub})"

			#print(f"Audio: {alang} {aid} " , f"Subtitles: {slang} {sid}")

			self.send_json({
				"audio": audio_info,
				"sub": subtitle_info
			})

		
# ... next method

		elif self.path.startswith("/status"):
			status = {
				"volume": mpv_get("volume"),
				"percent": mpv_get("percent-pos"),
				"duration": mpv_get("duration"),
			}
			self.send_json(status)
		elif self.path.startswith("/list?path="):
			path = unquote(self.path.split("=",1)[1])
			try:
				items = os.listdir(path)

				# --- START: Case-Insensitive Sorting ---
				# Sort directories and files by their lowercase version
				# to ensure case-insensitive ordering.
				dirs = sorted(
					[d for d in items if os.path.isdir(os.path.join(path, d))],
					key=str.lower
				)
				files = sorted(
					[f for f in items if os.path.isfile(os.path.join(path, f))],
					key=str.lower
				)
				# --- END: Case-Insensitive Sorting --

				items = dirs + files
			except Exception:
				items = []
			self.send_json(items)
		elif self.path.startswith("/isfile?path="):
			path = unquote(self.path.split("=",1)[1])
			self.send_json({"isFile": os.path.isfile(path)})


			
			
			

		elif self.path.startswith("/playlist_skip"):
			import urllib.parse
			q = urllib.parse.urlparse(self.path)
			params = urllib.parse.parse_qs(q.query)
			direction = params.get("dir", ["next"])[0]

			# Move playlist
			if direction == "prev":
				mpv_cmd(["playlist-prev"])
			else:
				mpv_cmd(["playlist-next"])

			# Give MPV time to update playlist-pos
			time.sleep(0.05)

			pos = mpv_get("playlist-pos")
			playlist = mpv_get("playlist")
			
			name = ""

			current_title = mpv_get("media-title") or mpv_get("filename")

			if current_title:
				name = current_title

			# Trim long names
			if len(name) > 50:
				name = name[:50] + "..."

			self.send_json({"name": name})
			return

		else:
			self.send_error(404)

	def send_html(self,html):
		data = html.encode()
		self.send_response(200)
		self.send_header("Content-Type","text/html")
		self.send_header("Content-Length",len(data))
		self.end_headers()
		self.wfile.write(data)

	def send_text(self,text):
		data=text.encode()
		self.send_response(200)
		self.send_header("Content-Type","text/plain")
		self.send_header("Content-Length",len(data))
		self.end_headers()
		self.wfile.write(data)

	def send_json(self,obj):
		data=json.dumps(obj).encode()
		self.send_response(200)
		self.send_header("Content-Type","application/json")
		self.send_header("Content-Length",len(data))
		self.end_headers()
		self.wfile.write(data)

# ----------------- START SERVER -----------------
def get_local_ip():
	s = S_socket.socket(S_socket.AF_INET, S_socket.SOCK_DGRAM)
	try:
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except Exception:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP


if start_mpv_if_needed():
	local_ip = get_local_ip()
	print("---------------------------------------------")
	print(f"[SUCCESS] MPV Remote Web Interface running at:")
	print(f"Open in Web Browser: http://{local_ip}:{PORT}")
	print(f"Mpv started: 'mpv --input-ipc-server={MPV_SOCKET} --idle --no-terminal'")
	print(f"Do not close mpv.")
	print(f"To stop server use CTRL Z, or CTRL C")
	#print(f"   -> http://127.0.0.1:{PORT}")
	print("---------------------------------------------")


	with HTTPServer((HOST, PORT), Handler) as srv:
		try:
			srv.serve_forever()
		except KeyboardInterrupt:
			fn_terminate_mpv()
			fn_terminate_python()
			print("\nServer stopped.")

else:
	print("\nServer startup aborted due to MPV launch failure.")
	fn_terminate_mpv()
	fn_terminate_python()