import sys, ast, operator, requests, json, requests, threading, random, re, json, tempfile, subprocess, os, time, pygame
import tkinter as tk
from tkinter import ttk
from PIL import Image
from tkinter.filedialog import askopenfilename, asksaveasfilename
pygame.init()
screen = None
window_running = False

digit_map = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
}
reverse_digit_map = {v: k for k, v in digit_map.items()}

possible_events = {
	"q": pygame.K_q,
	"w": pygame.K_w,
	"e": pygame.K_e,
	"r": pygame.K_r,
	"t": pygame.K_t,
	"y": pygame.K_y,
	"u": pygame.K_u,
	"i": pygame.K_i,
	"o": pygame.K_o,
	"p": pygame.K_p,
	"a": pygame.K_a,
	"s": pygame.K_s,
	"d": pygame.K_d,
	"f": pygame.K_f,
	"g": pygame.K_g,
	"h": pygame.K_h,
	"j": pygame.K_j,
	"k": pygame.K_k,
	"l": pygame.K_l,
	"z": pygame.K_z,
	"x": pygame.K_x,
	"c": pygame.K_c,
	"v": pygame.K_v,
	"b": pygame.K_b,
	"n": pygame.K_n,
	"m": pygame.K_m
}



command_map = {
		"decree": "Ω",
		"if": "╪",
		"end if": "▒",
		"while": "□",
		"for": "◊",
		"end loop": "◙",
		"function": "ꜛ",
		"end function": "ꜜ"
}
reverse_map = {v: k for k, v in command_map.items()}
IF_KEYWORDS = ["end if", "if", "else", "elif"]
LOOP_KEYWORDS = ["while", "skip", "end loop", "for"]
KEYWORDS = ["declare", "halt", "clear", "and", "or"]
VARIABLE_KEYWORDS = ["decree", "ask", "length", "at", "split"]
FUNCTION_KEYWORDS = ["function", "run", "end function"]
WINDOW_KEYWORDS = ["open window", "background", "tile background", "fill background", "wait", "close window"]
SPRITE_KEYWORDS = ["spawn", "resize", "change", "delete", "is colliding"]

def rgb_2_hex(r, g, b):
	return f"#{r:02x}{g:02x}{b:02x}"
back = rgb_2_hex(20, 30, 50)
misc_col    = rgb_2_hex(210, 160, 210)   
if_col      = rgb_2_hex(150, 230, 170)  
loop_col    = rgb_2_hex(240, 150, 120)   
varlog_col  = rgb_2_hex(170, 150, 230)   
func_col    = rgb_2_hex(235, 205, 120)   
window_col  = rgb_2_hex(150, 210, 240)   
sprite_col = rgb_2_hex(235, 120, 110)

class Sprite:
	def __init__(self, name, img, x, y, collisions=False):
		self.name = name
		self.img = img
		self.x = x
		self.y = y
		self.collisions = collisions

def escape_vbs(s: str) -> str:
	return s.replace('"', '""')

def popup(message, title="message", buttons=0):
	message = escape_vbs(message)
	title = escape_vbs(title)
	with tempfile.NamedTemporaryFile(delete=False, suffix=".vbs") as tmp:
		vbs_path = tmp.name
		tmp.write(f'''
MsgBox "{message}", {buttons}, "{title}"
'''.strip().encode("utf-8"))

	subprocess.Popen(["wscript.exe", vbs_path])

	time.sleep(0.1)

	os.remove(vbs_path)


def get_current_editor(notebook, window):
	current_tab = notebook.select()
	if current_tab:
		tab_index = notebook.index(current_tab)
		return window.tabs[tab_index]["text_edit"]
	return None

def is_dark(hex_colour):
	hex_colour = hex_colour.lstrip("#")
	r = int(hex_colour[0:2], 16)
	g = int(hex_colour[2:4], 16)
	b = int(hex_colour[4:6], 16)
	brightness = (0.299*r + 0.587*g + 0.114*b)
	return brightness < 128

def set_current_colour(colour, sprite_tab_index):
	tab = window.sprite_tabs[sprite_tab_index]
	tab["current_colour"] = colour

	for c, btn in tab["palette_buttons"].items():
		if c == colour:
			border_col = "white" if is_dark(c) else "black"
			btn.itemconfig("border", outline=border_col)
		else:
			btn.itemconfig("border", outline="")

sprites = []
background_col = "black"
keys = pygame.key.get_pressed()

def return_x_and_y(name, param):
	global sprites
	for sprite in sprites:
		if sprite.name == name:
			if param == "x":
				return sprite.x
			elif param == "y":
				return sprite.y
			else:
				print("Error: Invalid syntax for get x/y, must be: get <sprite> <x/y>")

def percentage_resize(width, height, percent):
	new_width = int(width * percent / 100)
	new_height = int(width * percent / 100)
	return new_width, new_height

def resize(name, percent):
	global sprites
	for sprite in sprites:
		if sprite.name == name:
			old_width = sprite.img.get_width()
			old_height = sprite.img.get_height()

			width, height = percentage_resize(old_width, old_height, percent)
			new_image = pygame.transform.scale(sprite.img, (width, height))
			sprite.img = new_image

def open_window(width, height, variables):
	global screen, window_running, sprites, background_col, keys, collided
	
	if window_running:
		popup("Window already running", "Error", "vbCritical")
		return

	window_running = True

	def run(variables):
		global screen, window_running, sprites, background_col, keys, collided
		screen = pygame.display.set_mode((width, height))
		clock = pygame.time.Clock()
		running = True
		
		while running:
			collided.clear()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					variables["__halt__"] = True
					running = False
				elif variables["__py_exit__"]:
					variables["__halt__"] = True
					running = False
				
			if running:
				keys = pygame.key.get_pressed()
			else:
				keys = [0] * 512

			
			if isinstance(background_col, pygame.Surface):
				screen.blit(background_col, (0, 0))
			else:
				screen.fill(background_col)

			current_sprites = sprites[:]

			for s in sprites:
				try:
					screen.blit(s.img, (float(s.x), float(s.y)))
				except pygame.error:
					continue

			pygame.display.update()
			
			pygame.display.flip()
			clock.tick(120)
		pygame.quit()
		window_running = False
	threading.Thread(target=run, args=(variables,), daemon=True).start()

def is_colliding(sprite_1, sprite_2):
	if sprite_1 is None:
		print(f"Error: No sprite provided")
		return False
	if sprite_2 is None:
		print(f"Error: No sprite provided")
		return False

	img_1 = sprite_1.img
	img_2 = sprite_2.img

	width_1 = img_1.get_width()
	width_2 = img_2.get_width()

	height_1 = img_1.get_height()
	height_2 = img_2.get_height()

	top_1 = sprite_1.y
	bottom_1 = sprite_1.y + height_1
	left_1 = sprite_1.x
	right_1 = sprite_1.x + width_1

	top_2= sprite_2.y
	bottom_2 = sprite_2.y + height_2
	left_2 = sprite_2.x
	right_2 = sprite_2.x + width_2

	collision_x = right_1 > left_2 and left_1 < right_2
	collision_y = bottom_1 > top_2 and top_1 < bottom_2

	return collision_x and collision_y




def check_for_event(ev):
	global keys, window_running
	if not window_running:
		return False	

	target_key_code = possible_events.get(ev.lower())

	if target_key_code is None:
		print(f"Error: Invalid key: {ev}")
		return False

	try:
		return keys[target_key_code]
	except (NameError, TypeError, pygame.error):
		return False


def spawn_sprite(name, x, y):
	global screen, sprites
	while screen == None:
		time.sleep(0.01)
	filepath = name + ".png"
	try:
		raw_img = pygame.image.load(filepath).convert_alpha()	
		content_rect = raw_img.get_bounding_rect()
		img = raw_img.subsurface(content_rect)
	except:
		print(f"Error: Invalid sprite name: {name}")
		return
	json_name = str(name)
	filepath = json_name + ".json"
	sprite_data = load_sprite_data(filepath)
	
	sprite = Sprite(name, img, x, y, collisions=sprite_data["collisions_var"])
	sprites.append(sprite)

def delete_sprite(name):
	global sprites, screen
	while screen is None:
		time.sleep(0.01)
	try:
		for sprite in sprites:
			if sprite.name == name:
				sprites.remove(sprite)

	except Exception as e:
		print(f"Error: {e}")
		return
collided = []
def move_sprite(name, axis, val):
	global sprites, collided
	for sprite in sprites:
		if sprite.name == name:
			old_x, old_y = sprite.x, sprite.y
			if axis == "x":
				sprite.x += val
			elif axis == "y":
				sprite.y += val
			else:
				print("Error: Invalid axis for sprite position editing, must be x or y")
				return
			collisions_detected = False
			for sp in sprites:
					if sp != sprite and sp.collisions:
						if is_colliding(sprite, sp):
							collisions_detected = True
							collided.append((sprite.name, sp.name))
			if collisions_detected:
				sprite.x, sprite.y = old_x, old_y				
			return



def render_pixels(window, 	tab_index):
	tab = window.sprite_tabs[tab_index]
	canvas = tab["canvas"]
	pixels = tab["pixels"]
	cell = tab["cell_size"]

	for y, row in enumerate(pixels):
		for x, colour in enumerate(row):
			if colour:
				canvas.itemconfig(f"cell_{y}_{x}", fill=colour)
			else:
				canvas.itemconfig(f"cell_{y}_{x}", fill="")

def load_sprite_data(json_filepath):
	try:
		with open(json_filepath, "r") as f:
			sprite_data = json.load(f)
		return sprite_data
	except FileNotFoundError:
		popup("File not found: {json_filepath}", "Error", "vbCritical")
		return None
	except json.JSONDecodeError:
		popup("Invalid JSON in: {json_filepath}", "Error", "vbCritical")
		return None

def load_sprite_pixels(sprites_notebook, window):
	filepath = askopenfilename(filetypes=[("JSON Files", "*.json")])
	if not filepath:
		return
	sprite_data = load_sprite_data(filepath)
	if not sprite_data:
		return
	
	idx = add_new_sprite_tab(sprites_notebook, window)
	tab = window.sprite_tabs[idx]
	tab["grid_var"].set(f"{sprite_data['width']}x{sprite_data['height']}")
	tab["build_canvas"]()
	sprites_notebook.select(idx)	
	tab = window.sprite_tabs[idx]
	
	tab["name_entry"].delete(0, tk.END)
	tab["name_entry"].insert(0, sprite_data["name"])

	tab["x_entry"].delete(0, tk.END)
	tab["x_entry"].insert(0, sprite_data["game_x"])

	tab["y_entry"].delete(0, tk.END)
	tab["y_entry"].insert(0, sprite_data["game_y"])

	tab["collisions_var"].set(sprite_data["collisions_var"])

	tab["pixels"] = sprite_data["pixels"]
	


	render_pixels(window, idx)

	


def save_sprite_as_png(tab_index, window):
	tab = window.sprite_tabs[tab_index]
	pixels = tab["pixels"]
	width = tab["grid_width"]
	height = tab["grid_height"]

	name_entry = tab.get("name_entry")
	sprite_name = name_entry.get().strip() if name_entry else f"Sprite_{tab_index + 1}"

	filepath = asksaveasfilename(
		defaultextension=".png",
		initialfile=sprite_name,
		filetypes=[("PNG Image", "*.png")])
	if not filepath:
		return

	base_path = filepath.rsplit('.', 1)[0]
	png_path = base_path + ".png"
	json_path = base_path + ".json"

	img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	pixel_data = img.load()

	for y in range(height):
		for x in range(width):
			colour = pixels[y][x]

			if colour:

				colour = colour.lstrip("#")
				r = int(colour[0:2], 16)
				g = int(colour[2:4], 16)
				b = int(colour[4:6], 16)
				pixel_data[x, y] = (r, g, b, 255)
	img.save(png_path)

	x_entry = tab.get("x_entry")
	y_entry = tab.get("y_entry")

	sprite_data = {
		"name": sprite_name,
		"width": width,
		"height": height,
		"game_x": x_entry.get() if x_entry else 0,
		"game_y": y_entry.get() if y_entry else 0,
		"png_path": png_path,
		"json_path": json_path,
		"pixels": pixels,
		"collisions_var": tab["collisions_var"].get()
	}

	with open(json_path, "w") as f:
		json.dump(sprite_data, f, indent=2)

	return sprite_name, png_path, json_path

def paint_pixel(event, idx):
	move_cursor(event, idx)
	tab = window.sprite_tabs[idx]
	canvas = tab["canvas"]
	cell = tab["cell_size"]
	pixels = tab["pixels"]
	current_colour = tab["current_colour"]
	brush = tab["brush_cells"]

	grid_x = event.x // cell
	grid_y = event.y // cell

	for dy in range(brush):
		for dx in range(brush):
			x = grid_x + dx
			y = grid_y + dy

			if 0 <= x < tab["grid_width"] and 0 <= y < tab["grid_height"]:
				pixels[y][x] = current_colour
				canvas.itemconfig(f"cell_{y}_{x}", fill=current_colour)

def erase_pixel(event, idx):
	move_cursor(event, idx)
	tab = window.sprite_tabs[idx]
	canvas = tab["canvas"]
	cell = tab["cell_size"]
	brush = tab["brush_cells"]
	pixels = tab["pixels"]

	grid_x = event.x // cell
	grid_y = event.y // cell

	for dy in range(brush):
		for dx in range(brush):
			x = grid_x + dx
			y = grid_y + dy

			if 0 <= x < tab["grid_width"] and 0 <= y < tab["grid_height"]:
				pixels[y][x] = None
				canvas.itemconfig(f"cell_{y}_{x}", fill="")

def move_cursor(event, idx):
	if idx not in window.sprite_tabs:
		return
	tab = window.sprite_tabs[idx]
	canvas = tab["canvas"]
	cell = tab["cell_size"]
	brush = tab["brush_cells"]
	cursor_id = tab["cursor_id"]

	tab["last_mouse_x"] = event.x
	tab["last_mouse_y"] = event.y

	snapped_x = (event.x // cell) * cell
	snapped_y = (event.y // cell) * cell

	size = brush * cell

	canvas.coords(cursor_id,
				  snapped_x,
				  snapped_y,
				  snapped_x + size,
				  snapped_y + size)

def add_new_sprite_tab(sprites_notebook, window):
	global collisions_var
	grid_sizes = ["20x20", "30x30", "40x40", "50x50", "60x60", "70x70", "80x80", "90x90", "100x100", "110x110", "120x120", "130x130", "140x140", "150x150"]
	grid_var = tk.StringVar(value="20x20")

	tab_count = len(window.sprite_tabs)
	new_frame = tk.Frame(sprites_notebook, bg=back)
	sprites_notebook.add(new_frame, text=f"Sprite_{tab_count + 1}")
	tab_index = tab_count


	window.sprite_tabs[tab_index] = {
		"frame": new_frame,
		"canvas": None,
		"pixels": None,
		"grid_width": None,
		"grid_height": None,
		"cell_size": 20,
		"game_x": 0,
		"game_y": 0,
		"current_colour": "#FF0000",
		"name_entry": None,
		"x_entry": None,
		"y_entry": None
	}
	sprites_notebook.select(new_frame)

	props_frame = tk.Frame(new_frame, bg=back, height=5)
	props_frame.pack(side=tk.TOP, fill=tk.X)
	row1 = tk.Frame(props_frame, bg=back)
	row1.pack(fill=tk.X, padx=5, pady=3)
	tk.Label(row1, text="Name:", bg=back, fg="white").pack(side=tk.LEFT)
	name_entry = tk.Entry(row1, bg=back, fg="white", insertbackground="orange", width=15)
	name_entry.pack(side=tk.LEFT, padx=5)
	name_entry.insert(0, f"Sprite_{tab_count + 1}")
	window.sprite_tabs[tab_index]["name_entry"] = name_entry
	tk.Label(row1, text="Grid size:", bg=back, fg="white").pack(side=tk.LEFT, padx=(20,0))
	size_dropdown = ttk.Combobox(row1, textvariable=grid_var, values=grid_sizes, width=7, state="readonly")
	size_dropdown.pack(side=tk.LEFT, padx=5)
	row2 = tk.Frame(props_frame, bg=back)
	row2.pack(fill=tk.X, padx=5, pady=2)
	row3 = tk.Frame(props_frame, bg=back)
	row3.pack(fill=tk.X, padx=5, pady=2)

	tk.Label(row2, text="Game X:", bg=back, fg="white").pack(side=tk.LEFT)
	x_entry = tk.Entry(row2, bg=back, fg="white", insertbackground="orange", width=8)
	x_entry.pack(side=tk.LEFT, padx=5)
	x_entry.insert(0, "0")
	window.sprite_tabs[tab_index]["x_entry"] = x_entry

	tk.Label(row2, text="Game Y:", bg=back, fg="white").pack(side=tk.LEFT)
	y_entry = tk.Entry(row2, bg=back, fg="white", insertbackground="orange", width=8)
	y_entry.pack(side=tk.LEFT, padx=5)
	y_entry.insert(0, "0")
	window.sprite_tabs[tab_index]["y_entry"] = y_entry

	collisions_var = tk.BooleanVar(value=False)
	collisions_check = tk.Checkbutton(
		row3,
		text="Enable collisions",
		variable=collisions_var,
		bg="#2b2b2b",
		fg="white",
		selectcolor="#3c3f41",
		activebackground="#2b2b2b",
		activeforeground="white"
		)
	collisions_check.pack(side=tk.LEFT, padx=5)
	window.sprite_tabs[tab_index]["collisions_var"] = collisions_var

	editor_frame = tk.Frame(new_frame, bg=back)
	editor_frame.pack(fill=tk.BOTH, expand=True, padx=(0,10), pady=0)

	palette_column = tk.Frame(editor_frame, bg=back)
	palette_column.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=(0,10))


	
	canvas_frame = tk.Frame(editor_frame, bg=back)
	canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

	colour_frame1 = tk.Frame(palette_column, bg=back, height=50)
	colour_frame1.pack(side=tk.TOP, fill=tk.X, pady=2)


	
	palette = [
    "#000000", "#050505", "#0A0A0A", "#0F0F0F", "#141414", "#191919", "#1E1E1E", "#232323", "#282828", "#2D2D2D",
    "#323232", "#373737", "#3C3C3C", "#414141", "#464646", "#4B4B4B", "#505050", "#555555", "#5A5A5A", "#5F5F5F",
    "#646464", "#696969", "#6E6E6E", "#737373", "#787878", "#7D7D7D", "#828282", "#878787", "#8C8C8C", "#919191",
    "#969696", "#9B9B9B", "#A0A0A0", "#A5A5A5", "#AAAAAA", "#AFAFAF", "#B4B4B4", "#B9B9B9", "#BEBEBE", "#C3C3C3",
    "#C8C8C8", "#CDCDCD", "#D2D2D2", "#D7D7D7", "#DCDCDC", "#E1E1E1", "#E6E6E6", "#EBEBEB", "#F0F0F0", "#F5F5F5",

    "#330000", "#380000", "#3D0000", "#420000", "#470000", "#4C0000", "#510000", "#560000", "#5B0000", "#600000",
    "#660000", "#6B0000", "#700000", "#750000", "#7A0000", "#800000", "#850000", "#8A0000", "#8F0000", "#940000",
    "#990000", "#A00000", "#A70000", "#AE0000", "#B50000", "#BC0000", "#C30000", "#CA0000", "#D10000", "#D80000",
    "#DF0000", "#E60000", "#ED0000", "#F40000", "#FB0000", "#FF0A0A", "#FF1414", "#FF1E1E", "#FF2828", "#FF3232",
    "#FF3C3C", "#FF4646", "#FF5050", "#FF5A5A", "#FF6464", "#FF6E6E", "#FF7878", "#FF8282", "#FF8C8C", "#FF9696",

    "#331900", "#3A1D00", "#422200", "#4A2600", "#522B00", "#5A2F00", "#623300", "#6A3800", "#723C00", "#7A4100",
    "#824500", "#8A4900", "#924E00", "#9A5200", "#A25600", "#AA5B00", "#B25F00", "#BA6300", "#C26800", "#CA6C00",
    "#D27000", "#DA7500", "#E27900", "#EA7D00", "#F28200", "#FA8600", "#FF8A0A", "#FF9123", "#FF983C", "#FF9F55",
    "#FFA66E", "#FFAD87", "#FFB4A0", "#FFBBA9", "#FFC2B2", "#FFC9BB", "#FFD0C4", "#FFD7CD", "#FFDED6", "#FFE5DF",
    "#FFECE8", "#FFF3F1", "#FFF7F5", "#FFF9F7", "#FFF9F8", "#FFF9F9", "#FFF9FA", "#FFF9FB", "#FFF9FC", "#FFF9FD",

    "#333300", "#3A3A00", "#424200", "#4A4A00", "#525200", "#5A5A00", "#626200", "#6A6A00", "#727200", "#7A7A00",
    "#828200", "#8A8A00", "#929200", "#9A9A00", "#A2A200", "#AAAA00", "#B2B200", "#BABA00", "#C2C200", "#CACA00",
    "#D2D200", "#DADA00", "#E2E200", "#EAEA00", "#F2F200", "#FAFA00", "#FFFF0A", "#FFFF14", "#FFFF1E", "#FFFF28",
    "#FFFF32", "#FFFF3C", "#FFFF46", "#FFFF50", "#FFFF5A", "#FFFF64", "#FFFF6E", "#FFFF78", "#FFFF82", "#FFFF8C",
    "#FFFF96", "#FFFFA0", "#FFFFAA", "#FFFFB4", "#FFFFBE", "#FFFFC8", "#FFFFD2", "#FFFFDC", "#FFFFE6", "#FFFFF0",

    "#003300", "#003A00", "#004200", "#004A00", "#005200", "#005A00", "#006200", "#006A00", "#007200", "#007A00",
    "#008200", "#008A00", "#009200", "#009A00", "#00A200", "#00AA00", "#00B200", "#00BA00", "#00C200", "#00CA00",
    "#00D200", "#00DA00", "#00E200", "#00EA00", "#00F200", "#00FA00", "#0AFF0A", "#14FF14", "#1EFF1E", "#28FF28",
    "#32FF32", "#3CFF3C", "#46FF46", "#50FF50", "#5AFF5A", "#64FF64", "#6EFF6E", "#78FF78", "#82FF82", "#8CFF8C",
    "#96FF96", "#A0FFA0", "#AAFFAA", "#B4FFB4", "#BEFFBE", "#C8FFC8", "#D2FFD2", "#DCFFDC", "#E6FFE6", "#F0FFF0",

    "#000033", "#00003A", "#000042", "#00004A", "#000052", "#00005A", "#000062", "#00006A", "#000072", "#00007A",
    "#000082", "#00008A", "#000092", "#00009A", "#0000A2", "#0000AA", "#0000B2", "#0000BA", "#0000C2", "#0000CA",
    "#0000D2", "#0000DA", "#0000E2", "#0000EA", "#0000F2", "#0000FA", "#0A0AFF", "#1414FF", "#1E1EFF", "#2828FF",
    "#3232FF", "#3C3CFF", "#4646FF", "#5050FF", "#5A5AFF", "#6464FF", "#6E6EFF", "#7878FF", "#8282FF", "#8C8CFF",
    "#9696FF", "#A0A0FF", "#AAAAFF", "#B4B4FF", "#BEBEFF", "#C8C8FF", "#D2D2FF", "#DCDCFF", "#E6E6FF", "#F0F0FF",

    "#190033", "#1E003A", "#230042", "#28004A", "#2D0052", "#32005A", "#370062", "#3C006A", "#410072", "#46007A",
    "#4B0082", "#50008A", "#550092", "#5A009A", "#5F00A2", "#6400AA", "#6900B2", "#6E00BA", "#7300C2", "#7800CA",
    "#7D00D2", "#8200DA", "#8700E2", "#8C00EA", "#9100F2", "#9600FA", "#9E0AFF", "#A614FF", "#AE1EFF", "#B628FF",
    "#BE32FF", "#C63CFF", "#CE46FF", "#D650FF", "#DE5AFF", "#E664FF", "#EE6EFF", "#F678FF", "#FE82FF", "#FF8CFF",
    "#FF96FF", "#FFA0FF", "#FFAAFF", "#FFB4FF", "#FFBEFF", "#FFC8FF", "#FFD2FF", "#FFDCFF", "#FFE6FF", "#FFF0FF",

    "#330019", "#3A001E", "#420023", "#4A0028", "#52002D", "#5A0032", "#620037", "#6A003C", "#720041", "#7A0046",
    "#82004B", "#8A0050", "#920055", "#9A005A", "#A2005F", "#AA0064", "#B20069", "#BA006E", "#C20073", "#CA0078",
    "#D2007D", "#DA0082", "#E20087", "#EA008C", "#F20091", "#FA0096", "#FF0A9E", "#FF14A6", "#FF1EAE", "#FF28B6",
    "#FF32BE", "#FF3CC6", "#FF46CE", "#FF50D6", "#FF5ADE", "#FF64E6", "#FF6EEE", "#FF78F6", "#FF82FE", "#FF8CFF",
    "#FF96FF", "#FFA0FF", "#FFAAFF", "#FFB4FF", "#FFBEFF", "#FFC8FF", "#FFD2FF", "#FFDCFF", "#FFE6FF", "#FFF0FF",

    "#1A0F00", "#1F1200", "#241500", "#291800", "#2E1B00", "#331E00", "#382100", "#3D2400", "#422700", "#472A00",
    "#4C2D00", "#513000", "#563300", "#5B3600", "#603900", "#653C00", "#6A3F00", "#6F4200", "#744500", "#794800",
    "#7E4B00", "#834E00", "#885100", "#8D5400", "#925700", "#975A00", "#9C5D00", "#A16100", "#A66505", "#AB690A",
    "#B06D0F", "#B57114", "#BA7519", "#BF791E", "#C47D23", "#C98128", "#CE852D", "#D38932", "#D88D37", "#DD913C",
    "#E29541", "#E79946", "#EC9D4B", "#F1A150", "#F6A555", "#FBA95A", "#FFAD5F", "#FFB264", "#FFB769", "#FFBC6E",

    "#003333", "#003A3A", "#004242", "#004A4A", "#005252", "#005A5A", "#006262", "#006A6A", "#007272", "#007A7A",
    "#008282", "#008A8A", "#009292", "#009A9A", "#00A2A2", "#00AAAA", "#00B2B2", "#00BABA", "#00C2C2", "#00CACA",
    "#00D2D2", "#00DADA", "#00E2E2", "#00EAEA", "#00F2F2", "#00FAFA", "#0AFFFF", "#14FFFF", "#1EFFFF", "#28FFFF",
    "#32FFFF", "#3CFFFF", "#46FFFF", "#50FFFF", "#5AFFFF", "#64FFFF", "#6EFFFF", "#78FFFF", "#82FFFF", "#8CFFFF",
    "#96FFFF", "#A0FFFF", "#AAFFFF", "#B4FFFF", "#BEFFFF", "#C8FFFF", "#D2FFFF", "#DCFFFF", "#E6FFFF", "#F0FFFF"
]

	
	def paint_palette():
		palette_grid = tk.Frame(palette_column, bg=back)
		palette_grid.pack()	
		window.sprite_tabs[tab_index]["palette_grid"] = palette_grid
		window.sprite_tabs[tab_index]["palette_shown"] = True		
		columns = 25
		for i, colour in enumerate(palette):
			row = i // columns
			col = i % columns

			btn = tk.Canvas(
				palette_grid,
				width=20,
				height=20,
				bg=colour,
				highlightthickness=1,
				highlightbackground="white"
				)
			border = btn.create_rectangle(
				1, 1, 19, 19,
				outline="",
				width=4,
				tags="border")

			window.sprite_tabs[tab_index].setdefault("palette_buttons", {})[colour] = btn

			btn.grid(row=row, column=col, padx=2, pady=2)
			btn.bind("<Button-1>", lambda e, c=colour, i=tab_index: set_current_colour(c, i))
			
	
	def toggle_pallete():
		tab = window.sprite_tabs[tab_index]

		if tab.get("palette_shown", True):
			tab["palette_grid"].forget()
			palette_column.pack_forget()
			tab["palette_shown"] = False
			canvas_frame.pack_forget()
			canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
			tab["canvas"].pack_forget()
			tab["canvas"].pack(expand=True)
		else:
			palette_column.pack(side=tk.LEFT, fill=tk.Y)
			tab["palette_shown"] = True 
			canvas_frame.pack_forget()
			canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
			tab["canvas"].pack_forget()
			tab["canvas"].pack(side=tk.TOP)
			paint_palette()

	window.sprite_tabs[tab_index]["toggle_palette"] = toggle_pallete	

	paint_palette()

	def build_canvas(event=None):

		for widget in canvas_frame.winfo_children():
			widget.destroy()
		size_text = grid_var.get()
		grid_width, grid_height = map(int, size_text.split("x"))

		canvas_pixel_size = 700
		cell_size = canvas_pixel_size // grid_width
		canvas_width = grid_width * cell_size
		canvas_height = grid_height * cell_size

		canvas = tk.Canvas(
			canvas_frame,
			width=canvas_width,
			height=canvas_height,
			bg=rgb_2_hex(40, 50, 70),
			highlightthickness=0)

		canvas.pack(side=tk.TOP)
		window.sprite_tabs[tab_index]["canvas"] = canvas

		for i in range(grid_width + 1):
			x = i * cell_size
			canvas.create_line(x, 0, x, canvas_height, fill="#444444")

		for i in range(grid_height + 1):
			y = i * cell_size
			canvas.create_line(0, y, canvas_width, y, fill="#444444")

		for row in range(grid_height):
			for col in range(grid_width):
				x1 = col * cell_size
				y1 = row * cell_size
				x2 = x1 + cell_size
				y2 = y1 + cell_size

				rect = canvas.create_rectangle(
					x1, y1, x2, y2,
					fill="", outline="",
					tags=(f"cell_{row}_{col}", "cell")
					)

		pixels = []
		for row in range(grid_height):
			pixel_row = []
			for col in range(grid_width):
				pixel_row.append(None)
			pixels.append(pixel_row)

		window.sprite_tabs[tab_index]["pixels"] = pixels
		window.sprite_tabs[tab_index]["grid_width"] = grid_width
		window.sprite_tabs[tab_index]["grid_height"] = grid_height
		window.sprite_tabs[tab_index]["cell_size"] = cell_size
		window.sprite_tabs[tab_index]["canvas"] = canvas
		
		window.sprite_tabs[tab_index]["brush_cells"] = 1
		window.sprite_tabs[tab_index]["data"] = {
													"name": name_entry.get(),
													"x_pos": x_entry.get(),
													"y_pos": y_entry.get(),
													"g_width": grid_width,
													"grid_height": grid_height,
													"pixel_data": pixels
													}

		window.sprite_tabs[tab_index]["cursor_id"] = canvas.create_rectangle(
			0, 0, cell_size, cell_size, outline="white", width=1, tags="cursor") 

		canvas.bind("<Motion>", lambda e, idx=tab_index: move_cursor(e, idx))
		canvas.bind("<B1-Motion>", lambda e, idx=tab_index: move_cursor(e, idx))
		canvas.bind("<B3-Motion>", lambda e, idx=tab_index: move_cursor(e, idx))
		canvas.bind("<Leave>", lambda e: canvas.coords(window.sprite_tabs[tab_index]["cursor_id"], -100, -100, -100, -100))
		canvas.bind("<Button-1>", lambda e, idx=tab_index: paint_pixel(e, idx))
		canvas.bind("<B1-Motion>", lambda e, idx=tab_index: paint_pixel(e, idx))

		canvas.bind("<Button-3>", lambda e, idx=tab_index: erase_pixel(e, idx))
		canvas.bind("<B3-Motion>", lambda e, idx=tab_index: erase_pixel(e, idx))
		canvas.bind("<MouseWheel>", change_brush)
		size_dropdown.bind("<<ComboboxSelected>>", build_canvas)


	window.sprite_tabs[tab_index]["build_canvas"] = build_canvas
	
	window.sprite_tabs[tab_index]["grid_var"] = grid_var
	def set_brush_cells(n, idx=tab_index):
		window.sprite_tabs[tab_index]["brush_cells"] = n

	def change_brush(event, idx=tab_index):
		tab = window.sprite_tabs[idx]
		b = tab["brush_cells"]
		if event.delta > 0:
			b += 1
		else:
			b = max(1, b - 1)

		tab["brush_cells"] = b

		if "last_mouse_x" in tab:
			fake_event = type("Event", (), {})()
			fake_event.x = tab["last_mouse_x"]
			fake_event.y = tab["last_mouse_y"]
			move_cursor(fake_event, idx)

	

	return tab_index

def add_new_sprite_tab_setup(sprites_notebook, window):
	new_tab = add_new_sprite_tab(sprites_notebook, window)
	sprites_notebook.select(new_tab)
	window.sprite_tabs[new_tab]["build_canvas"]()

def add_new_tab(notebook, window):
	new_tab = tk.Frame(notebook, bg=back)
	tab_count = len(window.tabs)
	notebook.add(new_tab, text=f"Untitled{tab_count + 1}")

	text_edit = tk.Text(new_tab, font=("Helvetica", 12), bg=back, fg="white", insertbackground="orange")
	text_edit.pack(fill=tk.BOTH, expand=True)
	text_edit.tag_configure("if_statement", foreground=if_col)
	text_edit.tag_configure("loop", foreground=loop_col)
	text_edit.tag_configure("misc", foreground=misc_col)
	text_edit.tag_configure("variable", foreground="cyan")
	text_edit.tag_configure("variable_log", foreground=varlog_col)
	text_edit.bind("<KeyRelease>", lambda x: highlight_keywords(text_edit))
	text_edit.config(tabs=("24p",))
	window.tabs[tab_count] = {"text_edit": text_edit, "filepath": None}
	notebook.select(new_tab)

def close_current_sprite_tab(notebook, window):
	current_tab = sprites_notebook.select()
	if current_tab:
		tab_index = sprites_notebook.index(current_tab)

		if len(window.sprite_tabs) <= 1:
			return

		if tab_index in window.sprite_tabs:
			canvas = window.sprite_tabs[tab_index].get("canvas")
			if canvas:
				canvas.unbind("<Motion>")
				canvas.unbind("<B1-Motion>")
				canvas.unbind("<B3-Motion>")
				canvas.unbind("Leave")
				canvas.unbind("<Button-1>")
				canvas.unbind("<Button-3>")
				canvas.unbind("<MouseWheel")

		sprites_notebook.forget(current_tab)
		del window.sprite_tabs[tab_index]

		new_tabs = {}

		for i, (old_idx, tab_data) in enumerate(sorted(window.sprite_tabs.items())):
			new_tabs[i] = tab_data
		window.sprite_tabs = new_tabs

def close_current_tab(notebook, window):
	current_tab = notebook.select()
	if current_tab:
		tab_index = notebook.index(current_tab)

		if len(window.tabs) <= 1:
			return

		notebook.forget(current_tab)
		del window.tabs[tab_index]

		new_tabs = {}

		for i, (old_idx, tab_data) in enumerate(sorted(window.tabs.items())):
			new_tabs[i] = tab_data
		window.tabs = new_tabs

def ask_assistant(question_entry, assistant_output, text_edit):
	question = question_entry.get().strip()
	if not question:
		return

	question_entry.delete(0, tk.END)
	user_code = text_edit.get("1.0", tk.END).strip()

	assistant_output.config(state=tk.NORMAL)
	assistant_output.insert(tk.END, f"You: {question}\n")
	assistant_output.see(tk.END)
	assistant_output.config(state=tk.DISABLED)
	assistant_output.update()

	thread = threading.Thread(target=lambda: get_assistant_response(question, user_code, assistant_output))
	thread.daemon = True
	thread.start()

def get_assistant_response(question, user_code, assistant_output):

	system_prompt = """You are the LarryScript IDE Assistant.
Help users write, understand, and debug LarryScript code.

ONLY suggest features documented below. NEVER invent syntax.

═══════════════════════════════════════════════════════════════════
⚠️ CRITICAL RULES
═══════════════════════════════════════════════════════════════════
1. ONLY use syntax shown in this document
2. Check EVERY line against examples
3. If unsure, say "I'm not certain"
4. Break complex tasks into simple steps

═══════════════════════════════════════════════════════════════════
📋 LARRYSCRIPT COMPLETE SYNTAX
═══════════════════════════════════════════════════════════════════

──────────────────
VARIABLES
──────────────────
✓ decree x = 5
✓ decree name = "Alice"
✓ decree sum = x plus y
✓ decree diff = x minus y
✓ decree product = x times y
✓ decree quotient = x divide y
✓ decree name = ask "What's your name?"
✓ decree num = random between 1 and 10

ONE operation per line only
Operations: plus, minus, times, divide

❌ WRONG: decree x = a plus b times c
✓ RIGHT: Split into steps:
         decree temp = a plus b
         decree x = temp times c

──────────────────
OUTPUT (declare)
──────────────────
✓ declare "Hello World"
✓ declare "Count: " + x
✓ declare x
✓ declare x + " is the value"
✓ declare "X: " + x + " Y: " + y

declare handles ALL output:
- Strings: declare "text"
- Variables: declare varname
- String + variable: declare "text" + var
- Variable + string: declare var + " text"
- Mixed: declare "A" + x + " B" + y

❌ WRONG: print x
❌ WRONG: console.log(x)
❌ WRONG: proclaim x (command removed)

──────────────────
LISTS
──────────────────
✓ decree items = ["apple", "banana", "cherry"]
✓ decree items = []
✓ decree first = items at 0
✓ decree items at 1 = "mango"
✓ decree len = items length
✓ decree items2 = append "pear" to items
✓ decree parts = split text by ","

Accessing: decree <var> = <list> at <index>
Setting: decree <list> at <index> = <value>
Length: decree <var> = <list> length
Append: decree <newlist> = append <item> to <list>
Split: decree <list> = split <string> by "<delimiter>"

❌ WRONG: items[0]
❌ WRONG: items.length
❌ WRONG: items.append()

──────────────────
CONDITIONALS
──────────────────
✓ if x is equal to 5
      declare "Five!"
  end if

✓ if x is greater than 10
      declare "Big"
  elif x is equal to 5
      declare "Medium"
  else
      declare "Small"
  end if

✓ if x is equal to 5 and y is less than 10
      declare "Both true"
  end if

✓ if x is equal to 5 or y is equal to 10
      declare "At least one true"
  end if

Comparisons: equal, not equal, greater, less
Logical: and, or
ALWAYS end with: end if

❌ WRONG: if x == 5
❌ WRONG: if x > 5
❌ WRONG: else if (use elif)

──────────────────
LOOPS
──────────────────
✓ while x is less than 10
      decree x = x plus 1
  end loop

✓ while x is equal to 5 and y is less than 10
      declare "Loop"
  end loop

✓ for every i in 1 to 5
      declare "i = " + i
  end loop

✓ for every item in items
      declare item
  end loop

Use "for every" (not just "for")
ALWAYS end with "end loop"
Support and/or in while conditions

❌ WRONG: for i in 1 to 5
❌ WRONG: while x < 10
❌ WRONG: end while
❌ WRONG: end

──────────────────
FUNCTIONS
──────────────────
✓ function greet
      declare "Hello!"
  end function

✓ run greet

No parameters, no return values
End with "end function"

❌ WRONG: function greet(name)
❌ WRONG: return value

──────────────────
OTHER
──────────────────
✓ halt - Stop execution
✓ clear - Clear console (variables remain)
✓ skip - Skip loop iteration (loops only)

══════════════════════════════════════════════════════════════════
✅ COMPLETE WORKING EXAMPLES
══════════════════════════════════════════════════════════════════

Example 1: Count to 10
decree count = 0
while count is less than 10
    declare "Count: " + count
    decree count = count plus 1
end loop

Example 2: Using and/or
decree x = 5
decree y = 3
if x is equal to 5 and y is less than 10
    declare "Both conditions true"
end if

if x is equal to 10 or y is equal to 3
    declare "At least one true"
end if

Example 3: Guess the number
decree secret = random between 1 and 10
decree guess = ask "Guess (1-10):"
if guess is equal to secret
    declare "Correct!"
else
    declare "Wrong! It was " + secret
end if

Example 4: List operations
decree items = ["apple", "banana", "cherry"]
decree len = items length
decree i = 0
while i is less than len
    decree item = items at i
    declare "Item: " + item
    decree i = i plus 1
end loop

Example 5: Card game (CORRECT)
decree cards = ["Ace", "King", "Queen", "Jack"]
decree len = cards length
decree max = len minus 1
decree index = random between 0 and max
decree secret = cards at index
decree guess = ask "Guess the card:"
if guess is equal to secret
    declare "Correct! It was " + secret
else
    declare "Wrong! It was " + secret
end if

Example 6: For loop with range
for every i in 1 to 5
    declare "Number: " + i
end loop

Example 7: For loop with list
decree fruits = ["apple", "banana", "orange"]
for every fruit in fruits
    declare "Fruit: " + fruit
end loop

Example 8: Using skip
for every i in 1 to 10
    if i is equal to 5
        skip
    end if
    declare "Number: " + i
end loop

Example 9: Functions
function say_hello
    declare "Hello from function!"
end function

run say_hello

Example 10: Multiple output styles
decree name = "Alice"
declare "Hello"
declare "Name: " + name
declare name
declare name + " is here"
declare "User: " + name + " logged in"

══════════════════════════════════════════════════════════════════
🚫 DOES NOT EXIST
══════════════════════════════════════════════════════════════════
❌ proclaim (command was removed - use declare)
❌ print / console.log / cout
❌ Multiple operations: decree x = a plus b times c
❌ Math operators: +, -, *, /, ==, <, >
❌ Array indexing: items[0]
❌ Object properties: items.length
❌ Comments
❌ Function parameters
❌ Return statements
❌ else if (use elif)
❌ continue (use skip)
❌ break (use halt)

══════════════════════════════════════════════════════════════════
🔧 DEBUGGING CHECKLIST
══════════════════════════════════════════════════════════════════
1. Using +,-,*,/ instead of plus, minus, times, divide?
2. Using ==, <, > instead of is equal to, is less than?
3. Multiple operations in one line?
4. Using "proclaim"? (removed - use declare)
5. Loop ending with "end" instead of "end loop"?
6. Using "for" instead of "for every"?
7. Using items[0] instead of items at 0?
8. Conditional ending with "end if"?

══════════════════════════════════════════════════════════════════
📝 HOW TO RESPOND
══════════════════════════════════════════════════════════════════
When generating code:
1. Use ONLY documented syntax
2. Break complex operations into simple steps
3. Use declare for ALL output (proclaim removed)
4. Check mentally: does every line match an example?
5. wrap snippets with ```larryscript <code> ```

When debugging:
1. Identify specific incorrect line
2. Explain the error
3. Show corrected line
4. Reference example

══════════════════════════════════════════════════════════════════
Creator: Smugm00s3
══════════════════════════════════════════════════════════════════"""


	if user_code:
		prompt = f"User's code:\n'''\n{user_code}\n'''\n\nQuestion: {question}"
	else:
		prompt = f"Question: {question}"

	try:
		payload = {
			"model": "qwen2.5:14b",
			"prompt": prompt,
			"system": system_prompt,
			"stream": True
		}

		response = requests.post("http://localhost:11434/api/generate",
								 json=payload, 
								 stream=True, 
								 timeout=120)

		

		assistant_output.config(state=tk.NORMAL)
		assistant_output.delete("end-2l", "end-1l")
		assistant_output.insert(tk.END, "Assistant: ")
		assistant_output.see(tk.END)
		assistant_output.config(state=tk.DISABLED)

		answer = ""
		last_pos = assistant_output.index(tk.END)

		for line in response.iter_lines():
			if line:
				chunk = json.loads(line)
				if "response" in chunk:
					text_piece = chunk["response"]
					assistant_output.config(state=tk.NORMAL)
					start = assistant_output.index(tk.END)
					assistant_output.insert(tk.END, text_piece)
					end = assistant_output.index(tk.END)
					assistant_output.config(state=tk.DISABLED)
					
					highlight_range(assistant_output, start, end)
					assistant_output.see(tk.END)
					assistant_output.update()

				if chunk.get("done", False):
					break

		assistant_output.config(state=tk.NORMAL)
		assistant_output.insert(tk.END, "\n\n")
		assistant_output.config(state=tk.DISABLED)

		highlight_code_block(assistant_output)

	except requests.exceptions.ConnectionError:
		assistant_output.config(state=tk.NORMAL)
		assistant_output.delete("end-2l", "end-1l")
		assistant_output.insert(tk.END, "Assistant: Sorry, i couldnt connect to Ollama (try: ollama serve)\n\n")
		assistant_output.see(tk.END)
		assistant_output.config(state=tk.DISABLED)
	except Exception as e:
		assistant_output.config(state=tk.NORMAL)
		assistant_output.delete("end-2l", "end-1l")
		assistant_output.insert(tk.END, f"Assistant: Error: {str(e)}\n\n")
		assistant_output.see(tk.END)
		assistant_output.config(tk.DISABLED)


def highlight_range(text_widget, start, end):
	keywords = [
        "end if","if","else","elif",
        "while","skip","end loop","for",
        "declare","halt","clear","and","or",
        "decree","ask","length","at","split",
        "function","run","end function"
    	]

	content = text_widget.get(start, end)
	base_line = int(start.split('.')[0])

	for i, line in enumerate(content.split('\n')):
		tk_line = base_line + i

		for kw in keywords:
			for m in re.finditer(rf"\b{re.escape(kw)}\b", line):
				s = f"{tk_line}.{m.start()}"
				e = f"{tk_line}.{m.start()+len(kw)}"

				if kw in ["end if", "if", "else", "elif"]:
					text_widget.tag_add("if", s, e)
				elif kw in ["while", "skip", "end loop", "for"]:
					text_widget.tag_add("l", s, e)
				elif kw in ["declare", "halt", "clear", "and", "or"]:
					text_widget.tag_add("mis", s, e)
				elif kw in ["decree", "ask", "length", "at", "split"]:
					text_widget.tag_add("var_log", s, e)
				elif kw in ["function", "run", "end function"]:
					text_widget.tag_add("fun", s, e)

	text_widget.tag_configure("if", foreground=if_col)
	text_widget.tag_configure("l", foreground=loop_col)
	text_widget.tag_configure("mis", foreground=misc_col)
	text_widget.tag_configure("var", foreground="cyan")
	text_widget.tag_configure("var_log", foreground=varlog_col)
	text_widget.tag_configure("fun", foreground=func_col)

def highlight_keywords(text_edit, even=None):
	content = text_edit.get(1.0, tk.END)
	text_edit.tag_remove("if_statement", 1.0, tk.END)
	text_edit.tag_remove("loop", 1.0, tk.END)
	text_edit.tag_remove("misc", 1.0, tk.END)
	text_edit.tag_remove("variable_log", 1.0, tk.END)
	text_edit.tag_remove("variable", 1.0, tk.END)
	text_edit.tag_remove("window", 1.0, tk.END)
	text_edit.tag_remove("sprite", 1.0, tk.END)
	variables = set()
	
	for line in content.splitlines():
		if line.strip().startswith("decree"):
			parts = line.split()
			if len(parts) >= 3 and parts[2] == "=":
				var_name = parts[1]
				variables.add(var_name)
		elif line.strip().startswith("for"):
			parts = line.split()
			if len(parts) > 5 and parts[1] == "every":
				var_name = parts[2]
				variables.add(var_name)

	for kw in IF_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("if_statement", pos, end)
			start = end

	for kw in WINDOW_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("window", pos, end)
			start = end

	for kw in SPRITE_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("sprite", pos, end)
			start = end
	
	for kw in FUNCTION_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("func", pos, end)
			start = end

	for kw in LOOP_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("loop", pos, end)
			start = end

	for kw in KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("misc", pos, end)
			start = end

	for kw in VARIABLE_KEYWORDS:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{kw}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			end = f"{pos}+{len(kw)}c"
			text_edit.tag_add("variable_log", pos, end)
			start = end

	for var in variables:
		start = "1.0"
		while True:
			pos = text_edit.search(rf"\y{var}\y", start, stopindex=tk.END, regexp=True)
			if not pos:
				break
			line_num, char_num = map(int, pos.split('.'))
			line_start = f"{line_num}.0"
			line_end = f"{line_num}.end"
			line_text = text_edit.get(line_start, line_end)

			before_pos = line_text[:int(char_num)]
			single_quotes = before_pos.count("'")
			double_quotes = before_pos.count('"')

			inside_string = (single_quotes % 2 == 1) or (double_quotes % 2 == 1)

			end = f"{pos}+{len(var)}c"
			
			if not inside_string:
				text_edit.tag_add("variable", pos, end)
			start = end

def encode(text, shift=3):
	result=[]
	for line in text.splitlines():
		for cmd, symbol in command_map.items():
			if line.startswith(cmd):
				line = line.replace(cmd, symbol, 1)
		for ch in line:
			if ch.isalpha():
				base = ord('A') if ch.isupper() else ord('a')
				result.append(chr((ord(ch) - base + shift) % 26 + base))
			elif ch.isdigit():
				result.append(digit_map[ch])
			else:
				result.append(ch)
		result.append("\n")
	return "".join(result)


def decode(text, shift=3):
	lines = []
	for line in text.splitlines():
		decoded_chars = []
		for ch in line:
			if ch.isalpha():
				base = ord('A') if ch.isupper() else ord('a')
				decoded_chars.append(chr((ord(ch) - base - shift) % 26 + base))
			elif ch in reverse_digit_map:
				decoded_chars.append(reverse_digit_map[ch])
			else:
				decoded_chars.append(ch)
		decoded_line = "".join(decoded_chars)

		for symbol, cmd in reverse_map.items():
			if line.startswith(symbol):
				decoded_line = decoded_line.replace(symbol, cmd, 1)

		lines.append(decoded_line)
	return "\n".join(lines)

class ConsolRedirector:
	def __init__(self, widget):
		self.widget = widget

	def write(self, message):
		self.widget.insert(tk.END, message)
		self.widget.see(tk.END)

	def flush(self):
		pass

def save(window, text_edit):
	filepath = asksaveasfilename(defaultextension=".lsc", filetypes=[("LarryScript Files", "*.lsc*")])
	if not filepath:
		return
	with open(filepath, "w", encoding="utf-8") as f:
		content = text_edit.get(1.0, tk.END)
		encoded = encode(content)
		f.write(encoded)

	filename = filepath.split("/")[-1].split("\\")[-1]

	for tab_idx, tab_data in window.tabs.items():
		if tab_data["text_edit"] == text_edit:
			notebook = text_edit.master.master
			notebook.tab(tab_idx, text=filename)
			tab_data["filepath"] = filepath
			break

def Input(prompt="Enter value: "):
	global Input_bar, window
	var = tk.StringVar()
	print(prompt)
	def on_enter(event=None):
		var.set(Input_bar.get())
		Input_bar.delete(0, tk.END)
		Input_bar.unbind("<Return>")

	Input_bar.bind("<Return>", on_enter)
	Input_bar.focus_set()
	window.wait_variable(var)
	return var.get()

def open_file(window, text_edit):
	filepath = askopenfilename(filetypes=[("LarryScript Files", "*.lsc*")])

	if not filepath:
		return

	text_edit.delete(1.0,tk.END)
	with open(filepath, "r", encoding="utf-8") as f:
		encoded = f.read()
		decoded = decode(encoded)
		text_edit.insert(tk.END, decoded)
	window.title(filepath)

def eval(op_1, comp, op_2):
	try:
		op_1 = int(op_1)
		op_2 = int(op_2)
	except ValueError:
		op_1 = str(op_1)
		op_2 = str(op_2)

	if comp == "greater":
		return op_1 > op_2
	elif comp == "less":
		return op_1 < op_2
	elif comp == "equal":
		return op_1 == op_2
	elif comp == "not":
		return op_1 != op_2
	elif comp == "plus":
		ans = op_1 + op_2
		return int(ans)
	elif comp == "minus":
		ans = op_1 - op_2
		return int(ans)
	elif comp == "divide":
		ans = op_1 / op_2
		return int(ans)
	elif comp == "times":
		ans = op_1 * op_2
		return int(ans)	

def eval_condition(cond, variables):
	global collided
	cond = cond.strip()
	if cond.lower() == "true":
		return True

	if "is colliding" in cond:
		parts = cond.split()
		if len(parts) < 4:
			print("Error: Invalid syntax for colliding check, must be: if is colliding <sprite 1> <sprite 2>")
			return False
		
		name1 = str(parts[2])
		name2 = str(parts[3])
		sprite1 = [s for s in sprites if s.name == name1]
		sprite2 = [s for s in sprites if s.name == name2]
		for s1 in sprite1:
			for s2 in sprite2:
				if is_colliding(s1, s2):
					return True

		for pair in collided:
			if (name1 in pair) and (name2 in pair):
				return True


	if "key pressed" in cond:
		parts = cond.split()
		if not len(parts) == 3:
			print("Error: Invalid key name")
			return False
		ev = parts[2]
		ev = str(ev)
		return check_for_event(ev)

	if " and " in cond:
		parts = cond.split(" and ")
		return all(eval_condition(part, variables) for part in parts)
	elif " or " in cond:
		parts = cond.split(" or ")
		return any(eval_condition(part, variables) for part in parts)
	else:
		cond = cond.replace(" is ", " ")
		cond = cond.replace(" to ", " ")
		tokens = cond.split()
		var = tokens[0]
		comp = tokens[1]
		val = tokens[-1]
		var_val = variables.get(var, var)
		val_val = variables.get(val, val)

		if isinstance(val_val, str):
		    if (val_val.startswith('"') and val_val.endswith('"')) or \
		       (val_val.startswith("'") and val_val.endswith("'")):
		        val_val = val_val[1:-1]
		

		try:
			var_val = int(var_val)
			val_val = int(val_val)
			numeric = True
		except:
			numeric = False

		if numeric:
			a, b = var_val, val_val
		else:
			a, b = str(var_val), str(val_val)

		if comp == "greater":
			return a > b
		elif comp == "less":
			return a < b
		elif comp == "equal":
			return a == b
		elif comp == "not":
			return a != b

def starts_nested_block(line):
	return line.startswith("if") or line.startswith("for") or line.startswith("while")

def parse_block(block, start_index):
	if start_index >= len(block):
		return [], start_index
	header = block[start_index].strip()
	body = [header]
	i = start_index + 1

	while i < len(block):
		line = block[i].strip()

		if starts_nested_block(line):
			nested, new_i = parse_block(block, i)
			body.append(nested)
			i = new_i
			continue

		if header.startswith("if") and line.startswith("end if"):
			body.append(line)
			return body, i + 1

		if (header.startswith("for") or header.startswith("while")) and line.startswith("end loop"):
			body.append(line)
			return body, i + 1

		body.append(line)
		i += 1
	return body, i


def execute_block(block, consol_output, variables, functions):
	bline_id = 0
	while bline_id < len(block):
		
		if variables.get("__halt__"):
			break
		line = block[bline_id]

		if isinstance(line, list):
			sig = execute_block(line, consol_output, variables, functions)
			if sig == "CONTINUE":
				return "CONTINUE"
			bline_id += 1
			continue
		line = line.strip()

		if line.startswith("if"):
			current_block = []
			branches = []
			current_condition = line[len("if "):].strip()
			bline_id += 1

			while bline_id < len(block):
				current_line = block[bline_id]
				
				if isinstance(current_line, list):
					current_block.append(current_line)
					bline_id += 1
					continue


				current_line = current_line.strip()
				
				if current_line.startswith("elif"):
					branches.append((current_condition, current_block))
					current_condition = current_line[len("elif "):].strip()
					current_block = []
					bline_id += 1
					continue



				elif current_line.startswith("else"):
					branches.append((current_condition, current_block))
					current_condition = None
					current_block = []
					bline_id += 1
					continue


				elif current_line.startswith("end if"):
					branches.append((current_condition, current_block))
					bline_id += 1
					break

				elif starts_nested_block(current_line):
					nested, new_i = parse_block(block, bline_id)
					current_block.append(nested)
					bline_id = new_i
					
				else:
					current_block.append(current_line)
					bline_id += 1
			
			for cond, blk in branches:
				if cond is None:
					execute_block(blk, consol_output, variables, functions)
					
					break
				if eval_condition(cond, variables):
					execute_block(blk, consol_output, variables, functions)
					
					break
			continue

		elif line.startswith("for"):
			parts = line.split(" ")
			if "to" in line and len(parts) >= 7:
				rang = True
				var = parts[2]
				low = parts[4]
				high = parts[6]
				list_n = None
				
			elif len(parts) >= 5:
				rang = False
				var = parts[2]
				list_n = parts[4]
				low = high = None
			else:
				print(f"Error: Invalid for loop syntax at line {bline_id}")

			
			loop_block = []
			bline_id += 1			

			while bline_id < len(block):
				current_line = block[bline_id]

				if isinstance(current_line, list):
					loop_block.append(current_line)
					bline_id += 1
					continue


				current_line = current_line.strip()
				
				if starts_nested_block(current_line):
					nested, new_i = parse_block(block, bline_id)
					loop_block.append(nested)
					bline_id = new_i
					continue

				elif current_line.startswith("end loop"):
					bline_id += 1
					break
				else:
					loop_block.append(current_line)
					bline_id += 1

			loop_end = bline_id

			if rang:
				try:
					low = int(low)
					high = int(high) + 1
				except:
					print(f"Error: The bounds of a range must be integers at line {bline_id}.")
					low = 1
					high = 1
					
				for x in range(low, high):
					if variables.get("__halt__"):
						break
					variables[var] = x
					sig = execute_block(loop_block, consol_output, variables, functions)
					if sig == "CONTINUE":
						continue

			else:
				list_val = []
				if list_n:
					if list_n in variables:
						list_val = variables[list_n]
					try:
						list_val = list(list_val)
					except:
						print(f"Error: No list named {list_n} at line {bline_id}.")
						list_val = []
			
				for val in list_val:
					if variables.get("__halt__"):
						break
					variables[var] = val
					sig = execute_block(loop_block, consol_output, variables, functions)
					if sig == "CONTINUE":
						continue


			
			bline_id = loop_end
			continue

		elif line.startswith("while"):
			condition = line[5:].strip()
			loop_block = []
			bline_id += 1
			depth = 0

			while bline_id < len(block):
				current_line = block[bline_id]
				time.sleep(0.001)

				if isinstance(current_line, list):
					loop_block.append(current_line)
					bline_id += 1
					continue


				current_line = current_line.strip()

				if starts_nested_block(current_line):
				    nested, new_i = parse_block(block, bline_id)
				    loop_block.append(nested)
				    bline_id = new_i
				    continue

				elif current_line.startswith("end loop"):
					bline_id += 1
					break
				else:
					loop_block.append(current_line)
					bline_id += 1
			
			loop_end = bline_id
			
			while eval_condition(condition, variables):
				if variables.get("__halt__"):
					break

				sig = execute_block(loop_block, consol_output, variables, functions)
				if sig == "CONTINUE":
					continue
			bline_id = loop_end
			continue

		elif line.startswith("halt"):
			variables["__halt__"] = True
			break
		else:
			sig = run_line(line, consol_output, variables, functions)
			if sig == "CONTINUE":
				return "CONTINUE"
			bline_id += 1




def run_line(line, consol_output, variables, functions):
	global background_col, screen
	if not line or line in ["end if", "end loop", "else", "end"]:
		return
	
	if line.startswith("declare"):
		parts = line.split(" ", 1)
		text = parts[1]

		if "+" in text:
			segments = text.split("+")
			output = ""
			for seg in segments:
				seg = seg.strip()
				if seg.startswith("'") and seg.endswith("'") or seg.startswith('"') and seg.endswith('"'):
					output += seg[1:-1]
				else:
					if seg in variables:
						val = variables[seg]
						if isinstance(val, str) and ((val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'"))):
							val = val[1:-1]
						output += str(val)
					else:
						output += seg
			print(output)
		else:
			if text.startswith("'") and text.endswith("'") or text.startswith('"') and text.endswith('"'):
				print(text[1:-1])
			elif text in variables:
				val = variables[text]
				if isinstance(val, str) and ((val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"'))):
					val = val[1:-1]
				print(val)
			else:
				print(text)
				
		
	elif line.startswith("skip"):
		return "CONTINUE"
	
	elif line.startswith("clear"):
		consol_output.delete(1.0, tk.END)

	elif line.startswith("tile background"):
		while screen is None:
			time.sleep(0.01)
		parts = line.split()
		if len(parts) < 3:
			return
		img_name = parts[2]
		filepath = img_name + ".png"

		scale_multi = 1.0

		if len(parts) >= 4:
			try:
				raw_percent = parts[3].strip("%")
				scale_multi = int(raw_percent) / 100.0
			except:
				print(f"Error: Invalid tile percentage: {parts[3]}")

		try:
			raw_img = pygame.image.load(filepath).convert_alpha()
			
			content_rect = raw_img.get_bounding_rect()

			tile_img = raw_img.subsurface(content_rect).convert_alpha()

			if scale_multi != 1.0:
				new_w = int(tile_img.get_width() * scale_multi)
				new_h = int(tile_img.get_height() * scale_multi)

				tile_img = pygame.transform.smoothscale(tile_img, (new_w, new_h))

			tile_img = tile_img.convert_alpha()
			tw, th = tile_img.get_width(), tile_img.get_height()

			win_x = int(variables["__window_x__"])
			win_y = int(variables["__window_y__"])

			tiled_surface = pygame.Surface((win_x, win_y))

			for x in range(0, win_x, tw):
				for y in range(0, win_y, th):
					tiled_surface.blit(tile_img, (x, y))

			background_col = tiled_surface

		except Exception as e:
			print(f"Tiling failed: {e}")
			return



	elif line.startswith("fill background"):
		while screen is None:
			time.sleep(0.01)
		parts = line.split()
		if len(parts) < 3:
			return
		img_name = parts[2]
		filepath = img_name + ".png"
		
		try:
			
			img = pygame.image.load(filepath)

		except:

			print(f"Error: Invalid image name: {filepath}")
			return

		try:
			win_x = int(variables["__window_x__"])
			win_y = int(variables["__window_y__"])
		except:
			print("x and y not numbers :(")
		
		try:
			target_size = (win_x, win_y)

			try:
				scaled_img = pygame.transform.scale(img, target_size)
			except:
				scaled_img = pygame.transform.scale(img, target_size)

			background_col = scaled_img.convert_alpha()
		except Exception as e:
			print(f"Scaling failed: {e}")


	elif line.startswith("resize"):
		parts = line.split()
		if not len(parts) == 3:
			print("Error: Invalid syntax for resize, must be: resize <sprite> <percentage%>")
			return
		name = parts[1]
		percent = parts[2]

		name = str(name)
		percent = percent.strip("%")
		try:
			percent = int(percent)
			resize(name, percent)
		except:
			print("Error: Percentage for resize must be a number <num>%")
			return

	elif line.startswith("close"):
		if not line == "close window":
			print("Error: Invalid syntax, must be: close window")
			return
		variables["__py_exit__"] = True
			
	
	elif line.startswith("run"):
		parts = line.split(" ", 1)
		name = parts[1]
		
		if name in functions:
			func_data = functions.get(name)
			code = func_data["code"]
			func_vars = variables.copy()
			existing_vars = set(variables.keys())

			execute_block(code, consol_output, func_vars, functions)

			for key, value in func_vars.items():
				if key in existing_vars:
					variables[key] = value
				else:
					func_data["local_vars"][key] = value
		else:
			print(f"Error: Function: {name} has not yet been defined.")
	
	elif line.startswith("wait "):
		clean_line = line.strip()	
		try:
			parts = line.split()
			ms = int(parts[1])

			time.sleep(ms / 1000.0)
		except:
			pass

	elif line.startswith("change"):
		parts = line.split()
		if len(parts) < 5 or not parts[3] == "by":
			return
		name = parts[1]
		axis = parts[2]
		val = parts[4]
		
		name = str(name)
		axis = str(axis)

		try:
			val = int(val)
		except:
			print("Error: The value for change must be an integer")

		move_sprite(name, axis, val)

	elif line.startswith("spawn"):
		parts = line.split()
		if len(parts) < 6 or not (parts[2] == "x" and parts[4] == "y"):
			return

		x = parts[3].strip()
		y = parts[5].strip()
		name = parts[1].strip()

		try:
			x = int(x)
			y = int(y)
		except:
			
			return
		try:
			name = str(name)
		except:
			
			return
		spawn_sprite(name, x, y)

	elif line.startswith("delete"):
		parts = line.split()
		if len(parts) < 2:
			return

		name = parts[1].strip()
		try:
			name = str(name)
		except:
			return
		delete_sprite(name)
		


	elif line.startswith("background"):
		while screen is None:
			time.sleep(0.01)

		parts = line.split()
		if len(parts) < 2:
			return
		colour = parts[1].strip()
		if not colour in pygame.color.THECOLORS:
			print("Error: Invalid colour for background: {colour}")
			return
		
		background_col = colour

	elif line.startswith("open"):
		parts = line.split(" ")
		if not (parts[2] == "x" and parts[4] == "y"):
			print("Error: Invalid syntax for open window command, must be: open window x<int> y<int>")
			return

		x = parts[3]
		y = parts[5]
		variables["__window_x__"] = x
		variables["__window_y__"] = y
		try:
			x = int(x)
			y = int(y)
		except:
			print("Error: x and y for open window must be integers")
			return

		open_window(x, y, variables)

	elif line.startswith("decree"):
		parts = line.split(" ")
		if parts[2] == "=":
			name = parts[1]
			value = parts[3]
			rhs = " ".join(parts[3:])

			if "plus" in parts:
				op_1 = parts[3]
				op_2 = parts[5]
				if op_1 in variables:
					op_1 = variables[op_1]
				if op_2 in variables:
					op_2 = variables[op_2]
				try:
					op_1 = int(op_1)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_1}.")
				try:
					op_2 = int(op_2)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_2}.")
				variables[name] = eval(op_1, "plus", op_2)
			
			elif "minus" in parts:
				op_1 = parts[3]
				op_2 = parts[5]
				if op_1 in variables:
					op_1 = variables[op_1]
				if op_2 in variables:
					op_2 = variables[op_2]
				try:
					op_1 = int(op_1)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_1}.")
				try:
					op_2 = int(op_2)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_2}.")
				variables[name] = eval(op_1, "minus", op_2)
			
			elif "divide" in parts:
				op_1 = parts[3]
				op_2 = parts[5]
				if op_1 in variables:
					op_1 = variables[op_1]
				if op_2 in variables:
					op_2 = variables[op_2]
				try: 
					op_1 = int(op_1)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_1}.")
				try:
					op_2 = int(op_2)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_2}.")
				variables[name] = eval(op_1, "divide", op_2)
			
			elif "times" in parts:
				op_1 = parts[3]
				op_2 = parts[5]
				if op_1 in variables:
					op_1 = variables[op_1]
				if op_2 in variables:
					op_2 = variables[op_2]
				try:
					op_1 = int(op_1)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_1}.")
				try:
					op_2 = int(op_2)
				except Exception:
					print(f"Error: Operands must be integers or variables {op_2}.")
				variables[name] = eval(op_1, "times", op_2)

			elif "get" in parts:
				if not len(parts) == 6:
					return
				name = parts[4]
				param = parts[5]
				var_name = parts[1]
				var_name = str(var_name)
				name = str(name)
				param = str(param)

				variables[var_name] = return_x_and_y(name, param)



			elif value == "random":
				minimum = parts[5]
				maximum = parts[7]
				if minimum in variables:
					minimum = variables[minimum]
				if maximum in variables:
					maximum = variables[maximum]
				try:
					minimum = int(minimum)
					maximum = int(maximum)
				except ValueError:
					print("ERROR: The minimum and maximum values for random must be integers")
					return
				rand = random.randint(minimum, maximum)
				variables[name] = rand

			elif rhs.startswith("[") and rhs.endswith("]"):
				inner = rhs[1:-1].strip()
				if inner:
					elements = []
					for x in inner.split(","):
						x = x.strip()
						if x.startswith("'") or x.startswith('"'):
							x = x.strip('"').strip("'")
						else:
							try:
								x= int(x)
							except ValueError:
								pass
						elements.append(x)
				else:
					elements = []
				variables[name] = elements
				return

			elif len(parts) > 4 and parts[4] == "length":
				list_name = parts[3]
				name = parts[1]
				if list_name in variables and isinstance(variables[list_name], list):
					
					variables[name] = len(variables[list_name])
				return

			elif "append" in parts:
				append_index = parts.index("append")
				source_var = parts[3]
				new_item = parts[append_index + 1]

				if new_item.startswith("'") or new_item.startswith('"'):
					new_item = new_item.strip("'").strip('"')
				else:
					try:
						new_item = int(new_item)
					except:
						pass

				if source_var in variables and isinstance(variables[source_var], list):
					new_list = variables[source_var].copy()
					new_list.append(new_item)
					variables[name] = new_list
				return

			elif "split" in parts:
				split_index = parts.index("split")
				source_var = parts[3]
				delimiter = parts[split_index + 1].strip("'").strip('"')
				if not delimiter:
					delimiter = " "

				if source_var in variables:
					text = str(variables[source_var])
					result = [item.strip() for item in text.split(delimiter)]
					variables[name] = result
				return

			elif "at" in parts:
				at_index = parts.index("at")
				list_name = parts[3]
				index_str = parts[at_index + 1]
				if index_str in variables:
					index_str = variables[index_str]


				if list_name in variables:
					lst = variables[list_name]
					if isinstance(lst, list):
						try:
							index = int(index_str)
							if 0 <= index < len(lst):
								variables[name] = lst[index]
							else:
								print(f"Error: Index {index} out of range.")
						except:
							print("Error: Index must be an integer.")
				return

		


			elif value == "ask":
				try:
					prom_tokens = parts[4:]
					prom = " ".join(prom_tokens).strip("'").strip('"')

				except Exception:
					print("Error: Prompt must be a string, e.g. decree x = ask \"<prompt\"")
					prom = ""
				val = Input(prompt=prom + " ")
				variables[name] = val.strip()
			else:
				variables[name] = value.strip()

		elif len(parts) > 4 and parts[2] == "at" and parts[4] == "=":
			list_name = parts[1]
			index_str = parts[3]
			value = parts [5]

			if value.startswith('"') or value.startswith("'"):
				value = value.strip("'").strip('"')
			elif value in variables:
				value = variables[value]
			else:
				try:
					value = int(value)
				except:
					pass
			if list_name in variables:
				lst = variables[list_name]
				if isinstance(lst, list):
					try:
						index = int(index_str)
						if 0 <= index < len(lst):
							lst[index] = value
						else:
							print(f"Error: Index {index} out of range.")
					except:
						print(f"Error: Index must be an integer.")
			return


	elif line.startswith("if"):
		cond = line.strip("if ")
		return eval_condition(cond, variables)

		
	else:
		print(f"Error: Invalid syntax > {line}.")


def run_code(text_edit, consol_output):
	sprites.clear()
	consol_output.delete(1.0, tk.END)
	code = text_edit.get(1.0, tk.END).strip()
	lines = code.splitlines()   
	variables = {}
	functions = {}
	variables["__py_exit__"] = False
	main_block = []
	line_id = 0
	
	while line_id < len(lines):
		line = lines[line_id].strip()
		

		if line.startswith("function"):
			parts = line.split(" ", 1)
			name = parts[1]
			functions[name] = {
				"code": [],
				"local_vars": {},
			}
			bline_id = line_id + 1

			while bline_id < len(lines):
				current_line = lines[bline_id].strip()

				if current_line.startswith("end function"):
					line_id = bline_id + 1
					break
				else:
					functions[name]["code"].append(current_line)
					bline_id += 1
			else:
				line_id = bline_id

			raw = functions[name]["code"]
			parsed, _ = parse_block(["dummy"] + raw, 1)
			functions[name]["code"] = parsed
			continue

		
		main_block.append(line)
		line_id += 1

	parsed_main, _ = parse_block(["dummy"] + main_block, 1)
	execute_block(parsed_main, consol_output, variables, functions)




		
def main():
	global window, Input_bar, assistant_frame, save_button, save_sprite_btn, load_sprite_btn, open_button, assistant_visible, consol_scrollbar, consol_frame, toggle_button, sprites_visible, notebook, consol_output, sprites_notebook, sprites_button, new_tab_button, close_tab_button, new_sprite_button, close_sprite_button, palette_btn

	

	window = tk.Tk()
	window.title("Larry IDE")
	window.state("zoomed")
	window.rowconfigure(1, weight=1)
	window.columnconfigure(0, weight=1)
	
	notebook = ttk.Notebook(window)
	notebook.grid(row=1, column=0, sticky="nsew")
	sprites_notebook = ttk.Notebook(window)
	window.sprite_tabs = {}


	tab1 = tk.Frame(notebook, bg=back)
	notebook.add(tab1, text="untitled-1")
	style = ttk.Style()
	style.theme_use("clam")
	style.configure("TNotebook", background=back, borderwidth=0)


	text_edit = tk.Text(tab1, font=("Helvetica", 12), bg=back, fg="white",insertbackground="orange")
	text_edit.pack(fill=tk.BOTH, expand=True)
	text_edit.tag_configure("if_statement", foreground=if_col)
	text_edit.tag_configure("loop", foreground=loop_col)
	text_edit.tag_configure("misc", foreground=misc_col)
	text_edit.tag_configure("variable", foreground="cyan")
	text_edit.tag_configure("variable_log", foreground=varlog_col)
	text_edit.tag_configure("func", foreground=func_col)
	text_edit.tag_configure("window", foreground=window_col)
	text_edit.tag_configure("sprite", foreground=sprite_col)

	text_edit.bind("<KeyRelease>", lambda x: highlight_keywords(text_edit))
	text_edit.config(tabs=("24p",))

	window.tabs = {0: {"text_edit": text_edit, "filepath": None}}
	window.current_tab_index = 0
	
	
	consol_frame = tk.Frame(window, bd=2)
	consol_frame.grid(row=2, column=0, sticky="nsew")
	consol_scrollbar = tk.Scrollbar(consol_frame)
	consol_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
	consol_output = tk.Text(consol_frame,
							height=10, bd=5,
							bg=back, fg="white",
							wrap=tk.WORD,
							insertbackground="orange", 
							yscrollcommand=consol_scrollbar.set)
	consol_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	consol_scrollbar.config(command=consol_output.yview)
	
	assistant_frame = tk.Frame(window, bd=2, bg=back)

	assistant_scrollbar = tk.Scrollbar(assistant_frame)
	assistant_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	assistant_output = tk.Text(assistant_frame,
							   height=8, bd=5,
							   bg=back, fg="white",
							   font=("Helvetica", 12),
							   wrap=tk.WORD,
							   insertbackground="orange",
							   yscrollcommand=assistant_scrollbar.set)
	assistant_output.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
	assistant_scrollbar.config(command=assistant_output.yview)
	assistant_output.insert(tk.END, "Hello👋 I'm the Larryscript assistant, ask me anything about your code and I'll do my best to help! (please send error messages if possible, to help with debugging)\n\n")
	assistant_output.config(state=tk.DISABLED)

	question_frame = tk.Frame(assistant_frame, bg=back)
	question_frame.pack(side=tk.BOTTOM, fill=tk.X)

	question_label = tk.Label(question_frame, text="Ask:", bg=back, fg="white", font=("Helvetica", 10))
	question_label.pack(side=tk.LEFT, padx=5)

	question_entry = tk.Entry(question_frame, font=("Helvetica", 12),
							  bg=back, fg="white", insertbackground="orange")
	question_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
	ask_button = tk.Button(question_frame, text="Ask assistant",
						   command = lambda: ask_assistant(question_entry, assistant_output, text_edit))
	ask_button.pack(side=tk.LEFT, padx=5)

	Input_bar = tk.Entry(window, font=("Helvetica", 12),
                     bg=back, fg="white", insertbackground="orange", width=40)
	Input_bar.grid(row=5, column=0, sticky="ew")
	sys.stdout = ConsolRedirector(consol_output)

	frame = tk.Frame(window, bd=2, bg=back)
	
	def save_sprite_as_png_setup():
		current_tab = sprites_notebook.select()
		if current_tab:
			tab_index = sprites_notebook.index(current_tab)
			if tab_index in window.sprite_tabs:
				save_sprite_as_png(tab_index, window)


	new_tab_button = tk.Button(frame, text="  New Tab  ", command=lambda: add_new_tab(notebook, window))
	close_tab_button = tk.Button(frame, text="  Close Tab  ", command=lambda: close_current_tab(notebook, window))
	new_sprite_button = tk.Button(frame, text="  New Sprite  ", command=lambda: add_new_sprite_tab_setup(sprites_notebook, window))
	close_sprite_button = tk.Button(frame, text="  Close Sprite  ", command=lambda: close_current_sprite_tab(sprites_notebook, window))
	save_button = tk.Button(frame, text="  Save  ", command=lambda: save(window, text_edit))
	open_button = tk.Button(frame, text="  Open  ", command=lambda: open_file(window, text_edit))
	run_button = tk.Button(frame, text="  Run  ", command=lambda: run_code(text_edit, consol_output))
	toggle_button = tk.Button(frame, text="◀ Assistant", command=lambda: show_assistant(window))
	sprites_button = tk.Button(frame, text="  Sprites  ", command=lambda: toggle_sprites(window))
	save_sprite_btn = tk.Button(frame, text="  Save Sprite  ", command=lambda: save_sprite_as_png_setup())
	load_sprite_btn = tk.Button(frame, text="  Load Sprite  ", command=lambda: load_sprite_pixels(sprites_notebook, window))
	
	def toggle_current_palette():
		current_tab = sprites_notebook.select()
		if current_tab:
			tab_index = sprites_notebook.index(current_tab)
			if tab_index in window.sprite_tabs:
				window.sprite_tabs[tab_index]["toggle_palette"]()
	palette_btn = tk.Button(frame, text="Palette", command=toggle_current_palette)

	new_tab_button.grid(row=0, column=0, sticky="ew")
	close_tab_button.grid(row=0, column=1, padx=5, sticky="ew")
	save_button.grid(row=0, column=2, padx=2, sticky="ew")
	open_button.grid(row=0, column=3, padx=3, sticky="ew")
	run_button.grid(row=0, column =4, padx=2, sticky="ew")
	toggle_button.grid(row=0, column=5, padx=2, sticky="e")
	sprites_button.grid(row=0, column=6, padx=2, sticky="e")
	frame.grid(row=0, column=0, sticky="ew")
	
	window.bind("<Control-s>", lambda x: save(window, text_edit))
	window.bind("<Control-o>", lambda x: open_file(window, text_edit))
	window.bind("<Control-r>", lambda x: run_code(text_edit, consol_output))
	window.bind("<Control-t>", lambda x: add_new_tab(notebook, window))
	window.bind("<Control-w>", lambda x: close_current_tab(notebook, window))
	text_edit.bind("<KeyRelease>", lambda x: highlight_keywords(text_edit))
	assistant_visible = False
	sprites_visible = False
	window.mainloop()


def toggle_sprites(window):
	global sprites_button, sprites_visible, save_button, save_sprite_btn, load_sprite_btn, open_button, notebook, sprites_notebook, consol_frame, new_tab_button, close_tab_button, new_sprite_button, close_sprite_button, consol_output, palette_btn
	if sprites_visible:
		sprites_notebook.grid_forget()
		notebook.grid(row=1, column=0, sticky="nsew")
		sprites_button.config(text="  Sprites  ")
		new_tab_button.grid(row=0, column=0, sticky="ew")
		close_tab_button.grid(row=0, column=1, padx=5, sticky="ew")
		consol_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		consol_frame.grid(row=2, column=0, sticky="nsew")
		consol_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		new_sprite_button.grid_forget()
		close_sprite_button.grid_forget()
		save_sprite_btn.grid_forget()
		save_button.grid(row=0, column=2, padx=2, sticky="ew")
		open_button.grid(row=0, column=3, padx=3, sticky="ew")
		load_sprite_btn.grid_forget()
		palette_btn.grid_forget()
		toggle_button.grid(row=0, column=5, padx=2, sticky="e")
		sprites_visible = False
	else:
		notebook.grid_forget()
		sprites_notebook.grid(row=1, column=0, sticky="nsew")
		sprites_button.config(text="  Scripts  ")
		new_tab_button.grid_forget()
		close_tab_button.grid_forget()
		consol_output.pack_forget()
		consol_scrollbar.pack_forget()
		consol_frame.grid_forget()
		new_sprite_button.grid(row=0, column=0, sticky="ew")
		close_sprite_button.grid(row=0, column=1, padx=5, sticky="ew")
		open_button.grid_forget()
		load_sprite_btn.grid(row=0, column=3, padx=3, sticky="ew")

		save_button.grid_forget()
		save_sprite_btn.grid(row=0, column=2, padx=2, sticky="ew")
		
		toggle_button.grid_forget()
		palette_btn.grid(row=0, column=5, padx=2, sticky="e")
		sprites_visible = True



def show_assistant(window):
	global assistant_visible, assistant_frame, toggle_button
	if assistant_visible:
		assistant_frame.grid_forget()
		toggle_button.config(text="◀ Assistant")
		assistant_visible = False
		window.columnconfigure(1, weight=0)
		window.columnconfigure(0, weight=1)

	else:
		assistant_frame.grid(row=0, column=1, rowspan=6, sticky="nsew")
		window.columnconfigure(1, weight=1)
		toggle_button.config(text="Assistant ▶")
		assistant_visible = True

main()