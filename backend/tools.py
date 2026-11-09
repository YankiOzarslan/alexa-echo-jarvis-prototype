import asyncio
import subprocess
import datetime
import httpx

async def run_applescript(script: str) -> str:
    """Executes an AppleScript asynchronously and returns output."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
        return f"Error: {stderr.decode().strip()}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

async def set_mac_volume(level: int) -> str:
    """Sets Mac system volume between 0 and 100."""
    level = max(0, min(100, level))
    script = f"set volume output volume {level}"
    res = await run_applescript(script)
    if "Error" not in res:
        return f"Mac system volume set to {level}%."
    return res

async def get_system_status() -> str:
    """Retrieves Mac battery, time, and basic system info."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    battery_info = "Unknown"
    try:
        proc = await asyncio.create_subprocess_exec(
            "pmset", "-g", "batt",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().splitlines()
        if len(lines) > 1:
            battery_info = lines[1].strip()
    except Exception:
        pass
    
    return f"Current time: {now}. Battery status: {battery_info}."

async def open_application(app_name: str) -> tuple[bool, str]:
    """Opens any macOS application via 'open -a' with smart name resolution."""
    app_lower = app_name.lower().strip()
    mapping = {
        "antigravity": "Antigravity",
        "antigravitvi": "Antigravity",
        "antigraviti": "Antigravity",
        "anti gravity": "Antigravity",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",
        "cursor": "Cursor",
        "spotify": "Spotify",
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "safari": "Safari",
        "terminal": "Terminal",
        "iterm": "iTerm",
        "iterm2": "iTerm",
        "telegram": "Telegram",
        "finder": "Finder",
        "notes": "Notes",
        "notlar": "Notes",
        "calculator": "Calculator",
        "hesap makinesi": "Calculator",
    }
    target_app = mapping.get(app_lower, app_name)
    try:
        proc = await asyncio.create_subprocess_exec(
            "open", "-a", target_app,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if proc.returncode == 0:
            return True, f"Successfully opened {target_app} on your Mac."
    except Exception as e:
        print(f"Error opening application {target_app}: {e}")

    # Fallback: search via mdfind for exact .app match
    try:
        proc = await asyncio.create_subprocess_exec(
            "mdfind", f"kMDItemKind == 'Application' && kMDItemFSName == '*{app_name}*'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        lines = [line.strip() for line in stdout.decode().splitlines() if line.strip().endswith(".app")]
        if lines:
            app_path = lines[0]
            await asyncio.create_subprocess_exec("open", app_path)
            app_clean = os.path.basename(app_path).replace(".app", "")
            return True, f"Successfully opened {app_clean} on your Mac."
    except Exception:
        pass

    return False, f"Could not find or open {app_name} on your Mac."

async def get_weather(city: str = "Istanbul") -> str:
    """Fetches real-time weather using Open-Meteo free API."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # First geocode the city name
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_res = await client.get(geo_url)
            geo_data = geo_res.json()
            if not geo_data.get("results"):
                return f"Could not find coordinates for {city}."
            
            loc = geo_data["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            city_name = loc.get("name", city)

            # Fetch weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            weather_res = await client.get(weather_url)
            wdata = weather_res.json().get("current_weather", {})
            temp = wdata.get("temperature", "N/A")
            wind = wdata.get("windspeed", "N/A")
            return f"In {city_name}, current temperature is {temp}°C with wind speed {wind} km/h."
    except Exception as e:
        return f"Could not fetch weather: {str(e)}"

async def protocol_daddys_home() -> str:
    """Iconic Iron Man Protocol: Daddy's Home -> Set volume to 80% and blast Back in Black!"""
    import os
    # 1. Set volume to 80%
    await set_mac_volume(80)

    # 2. Check if Spotify is installed, otherwise launch YouTube Back in Black
    spotify_app = "/Applications/Spotify.app"
    if os.path.exists(spotify_app):
        script = '''
        tell application "Spotify"
            activate
            play track "spotify:track:08mG3Y1vljYA6bvJ4qiICv"
        end tell
        '''
        await run_applescript(script)
    else:
        # Fallback: Open AC/DC Back in Black in default browser
        proc = await asyncio.create_subprocess_exec(
            "open", "https://www.youtube.com/watch?v=pAgnJDJN4VA"
        )
        await proc.communicate()

    return "Protocol Back in Black initialized. Volume raised to 80 percent, sound systems engaged. Welcome home, Sir."

async def play_youtube(query: str) -> str:
    """Fast, non-blocking YouTube & podcast player that never times out."""
    import urllib.parse
    import re
    
    # Clean query from trigger words
    clean_q = re.sub(r'\b(on youtube|from youtube|youtube|youtubedan|youtubetan|play|çal|aç|open|launch|watch|listen to|bölümünü|bölüm|videosunu|podcastin|podcastini)\b', '', query, flags=re.IGNORECASE).strip()
    
    # If the user just wanted to open YouTube homepage:
    if not clean_q or clean_q.lower() in ["youtube", "open", "aç"]:
        await asyncio.create_subprocess_exec("open", "https://www.youtube.com")
        return "Opening YouTube on your Mac now, Sir."

    # Add "latest" or "full episode" if mentioned podcast
    search_terms = clean_q
    if "huberman" in clean_q.lower() and "latest" not in clean_q.lower() and "yeni" not in clean_q.lower():
        search_terms += " latest episode"

    encoded_query = urllib.parse.quote_plus(search_terms)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    target_url = search_url
    try:
        # Fast 2-second attempt to grab direct video ID
        async with httpx.AsyncClient(timeout=2.0, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}) as client:
            resp = await client.get(search_url)
            if resp.status_code == 200:
                matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
                for mid in matches:
                    if len(mid) == 11:
                        target_url = f"https://www.youtube.com/watch?v={mid}"
                        break
    except Exception as e:
        print(f"Fast YouTube lookup fallback to search URL: {e}")

    # Set Mac volume to 75%
    await set_mac_volume(75)

    # Launch immediately on Mac
    await asyncio.create_subprocess_exec("open", target_url)

    return f"Opening {clean_q} on YouTube on your Mac now, Sir."

async def execute_python_code(code: str) -> str:
    """Executes Python code directly on macOS and returns the output."""
    import re
    cleaned_code = re.sub(r'^```python\s*', '', code.strip())
    cleaned_code = re.sub(r'```$', '', cleaned_code).strip()
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-c", cleaned_code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=8.0)
        out = stdout.decode().strip()
        err = stderr.decode().strip()
        if proc.returncode == 0:
            return f"Execution successful. Output: {out}" if out else "Execution successful with no output."
        return f"Execution error: {err}"
    except asyncio.TimeoutError:
        return "Execution timed out after 8 seconds."
    except Exception as e:
        return f"Failed to execute code: {str(e)}"

async def open_in_vscode(filepath: str) -> bool:
    """Launches or opens the file directly inside Visual Studio Code."""
    try:
        proc = await asyncio.create_subprocess_exec("code", filepath)
        await proc.communicate()
        return True
    except Exception as e:
        print(f"Could not open in VS Code: {e}")
        return False

async def auto_create_and_open_script(task_description: str, code_content: str, filename: str = None) -> str:
    """Saves generated code directly to Desktop and opens it in VS Code."""
    import os
    import re

    if not filename:
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', task_description.lower())[:25].strip('_')
        filename = f"{clean_name}.py" if clean_name else "jarvis_script.py"

    if not filename.endswith(".py"):
        filename += ".py"

    desktop_path = os.path.expanduser("~/Desktop")
    filepath = os.path.join(desktop_path, filename)

    # Clean markdown fences and prefix artifacts
    clean_code = re.sub(r'^(?:LINE\s*1\s*:\s*)?(?:FILENAME\s*:\s*[^\n]+\n?)?', '', code_content.strip(), flags=re.IGNORECASE).strip()
    clean_code = re.sub(r'^```[a-zA-Z]*\s*\n', '', clean_code).strip()
    clean_code = re.sub(r'\n```\s*$', '', clean_code).strip()
    clean_code = re.sub(r'^(?:LINE\s*1\s*:\s*)?', '', clean_code, flags=re.IGNORECASE).strip()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean_code + "\n")

    # Automatically open in VS Code
    await open_in_vscode(filepath)

    return f"Script successfully engineered and saved to your Desktop as {filename}. I have also opened it in VS Code for your review, Sir."




