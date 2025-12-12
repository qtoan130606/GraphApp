import sys
import io
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, ttk
import math
import json

# --- FIX UTF-8 WINDOWS ---
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except AttributeError: pass

# --- IMPORT LOGIC ---
try:
    from graph_logic import GraphLogic
except ImportError:
    messagebox.showerror("Lỗi", "Thiếu file 'graph_logic.py'")
    sys.exit()

# --- CONFIG ---
NODE_R = 20
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#2d2d2d"
COLOR_NODE = "#4caf50"
COLOR_EDGE = "#ffffff"
COLOR_HIGHLIGHT = "#ffeb3b"
COLOR_PATH = "#f44336"
COLOR_MAP_BIPARTITE = {0: "#f44336", 1: "#2196f3"}

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Graph Master Ultimate - Fixed Version")
        self.root.geometry("1450x800")
        
        self.algo = GraphLogic()
        
        self.node_counter = 1
        self.selected_node = None
        self.edge_start = None
        self.drag_data = {"x": 0, "y": 0, "item": None}

        self._init_ui()

    def _init_ui(self):
        # LEFT PANEL
        left_panel = tk.Frame(self.root, width=220, bg=COLOR_PANEL)
        left_panel.pack(side=tk.LEFT, fill=tk.Y); left_panel.pack_propagate(False) 
        
        tk.Label(left_panel, text="CÔNG CỤ", bg=COLOR_PANEL, fg="#00ff00", font=("Arial", 11, "bold")).pack(pady=(10, 5))
        self._btn(left_panel, "Reset All", self.clear_all, "red")
        self._btn(left_panel, "Nhập Dữ Liệu (Text)", self.show_manual_input, "#9c27b0")
        self._btn(left_panel, "Lưu Graph (JSON)", self.save_graph)
        self._btn(left_panel, "Mở Graph (Load)", self.load_graph, "#009688")
        self._btn(left_panel, "Đổi: Vô Hướng/Có Hướng", self.toggle_directed, "blue")
        
        tk.Label(left_panel, text="THUẬT TOÁN CƠ BẢN", bg=COLOR_PANEL, fg="cyan", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        self._btn(left_panel, "BFS (Rộng)", lambda: self.run_algo('bfs'))
        self._btn(left_panel, "DFS (Sâu)", lambda: self.run_algo('dfs'))
        self._btn(left_panel, "Dijkstra (Ngắn nhất)", lambda: self.run_algo('dijkstra'))
        self._btn(left_panel, "Check 2 Phía", lambda: self.run_algo('bipartite'))

        tk.Label(left_panel, text="THUẬT TOÁN NÂNG CAO", bg=COLOR_PANEL, fg="orange", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        self._btn(left_panel, "Prim (MST)", lambda: self.run_algo('prim'))
        self._btn(left_panel, "Kruskal (MST)", lambda: self.run_algo('kruskal'))
        self._btn(left_panel, "Ford-Fulkerson", lambda: self.run_algo('ford'))
        
        tk.Label(left_panel, text="--- EULER ---", bg=COLOR_PANEL, fg="#aaa", font=("Arial", 8)).pack(pady=(5, 2))
        self._btn(left_panel, "Fleury", lambda: self.run_algo('fleury'))
        self._btn(left_panel, "Hierholzer", lambda: self.run_algo('hierholzer'))

        # RIGHT PANEL
        right_panel = tk.Frame(self.root, width=350, bg=COLOR_PANEL)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y); right_panel.pack_propagate(False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=COLOR_PANEL, borderwidth=0)
        style.configure("TNotebook.Tab", background="#444", foreground="white")
        
        self.tabs = ttk.Notebook(right_panel)
        self.tabs.pack(expand=True, fill="both", padx=5, pady=5)

        self.tab_logs = tk.Frame(self.tabs, bg=COLOR_PANEL)
        self.tabs.add(self.tab_logs, text="Nhật ký")
        self.log_text = tk.Text(self.tab_logs, bg="#111", fg="#00ff00", font=("Consolas", 10))
        self.log_text.pack(expand=True, fill="both")

        self.tab_data = tk.Frame(self.tabs, bg=COLOR_PANEL)
        self.tabs.add(self.tab_data, text="Dữ liệu")
        
        tk.Label(self.tab_data, text="1. MA TRẬN KỀ", bg=COLOR_PANEL, fg="white", font=("Arial", 8, "bold")).pack(anchor="w")
        self.txt_matrix = tk.Text(self.tab_data, bg="#222", fg="white", font=("Consolas", 9), height=8)
        self.txt_matrix.pack(fill="x", padx=2)
        
        tk.Label(self.tab_data, text="2. DANH SÁCH KỀ", bg=COLOR_PANEL, fg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(5,0))
        self.txt_adj = tk.Text(self.tab_data, bg="#222", fg="white", font=("Consolas", 9), height=8)
        self.txt_adj.pack(fill="x", padx=2)

        tk.Label(self.tab_data, text="3. DANH SÁCH CẠNH", bg=COLOR_PANEL, fg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(5,0))
        self.txt_edges = tk.Text(self.tab_data, bg="#222", fg="white", font=("Consolas", 9), height=8)
        self.txt_edges.pack(fill="both", expand=True, padx=2)

        # CANVAS
        self.canvas = tk.Canvas(self.root, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Connect Logic
        self.algo.canvas = self.canvas
        
        self.lbl_mode = tk.Label(self.canvas, text="CHẾ ĐỘ: VÔ HƯỚNG", bg=COLOR_BG, fg="#555", font=("Arial", 20, "bold"))
        self.lbl_mode.place(relx=0.5, rely=0.05, anchor="center")
        self.lbl_status = tk.Label(self.canvas, text="Ready...", bg=COLOR_BG, fg="yellow", anchor="w")
        self.lbl_status.place(relx=0, rely=0.97, relwidth=1)

        self.canvas.bind("<Button-1>", self.on_click_left)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_click_right)

        # Update initial UI state
        self.toggle_directed() # Gọi 1 lần để set label đúng
        self.toggle_directed() # Gọi lại lần 2 để về lại mode mặc định

    def _btn(self, parent, text, cmd, color="#555"):
        tk.Button(parent, text=text, command=cmd, bg=color, fg="white", relief="flat", width=25, font=("Arial", 9)).pack(pady=2)

    # --- ACTIONS ---
    def save_graph(self):
        save_adj = {str(k): {str(v): w for v, w in n.items()} for k, n in self.algo.adj.items()}
        save_nodes = {str(k): v for k, v in self.algo.nodes.items()}
        data = {"nodes": save_nodes, "adj": save_adj, "is_directed": self.algo.is_directed}
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if f:
            try:
                with open(f, "w", encoding='utf-8') as file: json.dump(data, file, indent=4, ensure_ascii=False)
                self.log(f"Đã lưu: {f}")
            except Exception as e: messagebox.showerror("Lỗi", str(e))
            
    def load_graph(self):
        # 1. Mở hộp thoại chọn file
        f = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not f: return # Người dùng bấm Cancel thì thôi

        try:
            with open(f, "r", encoding='utf-8') as file:
                data = json.load(file)

            # 2. Dọn sạch đồ thị cũ
            self.clear_all()

            # 3. Khôi phục chế độ (Có hướng/Vô hướng)
            # Lưu ý: Cần ép kiểu bool để chắc chắn
            is_directed = bool(data.get("is_directed", False))
            self.algo.set_mode(is_directed)
            
            # Cập nhật lại cái nhãn trên màn hình cho khớp
            txt_mode = "CHẾ ĐỘ: CÓ HƯỚNG" if is_directed else "CHẾ ĐỘ: VÔ HƯỚNG"
            self.lbl_mode.config(text=txt_mode)

            # 4. Tái tạo các Node (Đỉnh)
            # data["nodes"] có dạng: { "1": [100, 200], "2": [300, 400] }
            loaded_nodes = data.get("nodes", {})
            max_id = 0
            for nid, pos in loaded_nodes.items():
                x, y = pos
                self.algo.add_node(str(nid), x, y)
                
                # Cập nhật biến đếm ID để khi tạo node mới không bị trùng
                if str(nid).isdigit():
                    max_id = max(max_id, int(nid))
            
            self.node_counter = max_id + 1

            # 5. Tái tạo các Edge (Cạnh)
            # data["adj"] có dạng: { "1": {"2": 10}, "2": {"3": 5} }
            adj_data = data.get("adj", {})
            for u, neighbors in adj_data.items():
                for v, w in neighbors.items():
                    # Lưu ý: add_edge trong logic của ông có thể tự lọc trùng nếu là vô hướng
                    self.algo.add_edge(str(u), str(v), int(w))

            # 6. Vẽ lại & Báo cáo
            self.draw_graph()
            self.update_data_view()
            self.log(f"Đã load xong file: {f}")

        except Exception as e:
            messagebox.showerror("Lỗi Load File", f"File hỏng hoặc sai định dạng!\n{str(e)}")

    def show_manual_input(self):
        win = tk.Toplevel(self.root)
        win.title("Nhập Dữ Liệu")
        win.geometry("400x500")
        win.configure(bg=COLOR_PANEL)
        tk.Label(win, text="Nhập u v w:", bg=COLOR_PANEL, fg="white").pack(pady=5)
        txt = tk.Text(win, bg="#111", fg="#00ff00", insertbackground="white", height=15)
        txt.pack(padx=10, pady=5, fill="both", expand=True)
        def on_confirm():
            raw = txt.get("1.0", tk.END).strip()
            if not raw: return
            self.process_manual_data(raw)
            win.destroy()
        tk.Button(win, text="VẼ", command=on_confirm, bg="#4caf50", fg="white").pack(fill="x", padx=10, pady=10)

    def process_manual_data(self, data_str):
        self.clear_all()
        lines = data_str.split('\n')
        nodes_set = set(); edges = []
        try:
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 2: continue
                u, v = parts[0], parts[1]
                w = int(parts[2]) if len(parts) > 2 else 1
                nodes_set.add(u); nodes_set.add(v)
                edges.append((u, v, w))
            
            nodes_list = sorted(list(nodes_set))
            count = len(nodes_list)
            cx, cy = 600, 400; radius = 250
            if count > 0:
                angle_step = 2 * math.pi / count
                for i, nid in enumerate(nodes_list):
                    angle = i * angle_step
                    x = cx + int(radius * math.cos(angle))
                    y = cy + int(radius * math.sin(angle))
                    self.algo.add_node(nid, x, y)
                    if nid.isdigit(): self.node_counter = max(self.node_counter, int(nid) + 1)
            for u, v, w in edges: self.algo.add_edge(u, v, w)
            self.draw_graph(); self.update_data_view()
        except Exception as e: messagebox.showerror("Lỗi", str(e))

    def update_data_view(self):
        nodes, mat = self.algo.get_matrix()
        self.txt_matrix.delete(1.0, tk.END)
        if nodes:
            header = "   " + " ".join([f"{n:>3}" for n in nodes]) + "\n"
            self.txt_matrix.insert(tk.END, header)
            for i, row in enumerate(mat):
                self.txt_matrix.insert(tk.END, f"{nodes[i]:>3} " + " ".join([f"{x:>3}" for x in row]) + "\n")

        self.txt_adj.delete(1.0, tk.END)
        for u in self.algo.adj:
            line = f"{u}: " + ", ".join([f"{v}({w})" for v, w in self.algo.adj[u].items()]) + "\n"
            self.txt_adj.insert(tk.END, line)

        self.txt_edges.delete(1.0, tk.END)
        edges = self.algo.get_edge_list()
        for u, v, w in edges:
            arrow = "->" if self.algo.is_directed else "--"
            self.txt_edges.insert(tk.END, f"{u} {arrow} {v} (w={w})\n")

    def log(self, msg):
        self.lbl_status.config(text=str(msg))
        self.log_text.insert(tk.END, ">> " + str(msg) + "\n")
        self.log_text.see(tk.END)

    def toggle_directed(self):
        # [FIX] Logic chuẩn: Rebuild graph
        new_mode = not self.algo.is_directed
        self.algo.set_mode(new_mode)
        
        self.draw_graph(); self.update_data_view()
        txt = "CHẾ ĐỘ: CÓ HƯỚNG" if self.algo.is_directed else "CHẾ ĐỘ: VÔ HƯỚNG"
        self.lbl_mode.config(text=txt)
        self.log(f"Đã chuyển sang: {txt}")

    # --- EVENTS ---
    def on_click_left(self, event):
        clicked = self.get_node_at(event.x, event.y)
        if clicked:
            self.drag_data["item"] = clicked; self.drag_data["x"] = event.x; self.drag_data["y"] = event.y
        else:
            nid = str(self.node_counter)
            self.algo.add_node(nid, event.x, event.y)
            self.node_counter += 1
            self.draw_graph(); self.update_data_view()

    def on_drag(self, event):
        nid = self.drag_data["item"]
        if nid:
            self.algo.nodes[nid] = (event.x, event.y)
            self.draw_graph()

    def on_release(self, event): self.drag_data["item"] = None

    def on_click_right(self, event):
        target = self.get_node_at(event.x, event.y)
        if target:
            if self.edge_start and self.edge_start != target:
                w = simpledialog.askinteger("Weight", "Trọng số:", initialvalue=1)
                if w is not None: self.algo.add_edge(self.edge_start, target, w)
                self.edge_start = None; self.draw_graph(); self.update_data_view()
            else:
                m = tk.Menu(self.root, tearoff=0)
                m.add_command(label=f"Nối cạnh từ {target}...", command=lambda: self.start_connect(target))
                m.add_separator()
                m.add_command(label=f"XÓA Node {target}", command=lambda: self.delete_node(target), foreground="red")
                m.tk_popup(event.x_root, event.y_root)
        else:
            if self.edge_start: self.edge_start = None; self.draw_graph()

    def start_connect(self, node):
        self.edge_start = node; self.draw_graph()
        self.log(f"Chọn nối từ {node}...")

    def delete_node(self, node):
        self.algo.remove_node(node)
        if self.edge_start == node: self.edge_start = None
        self.draw_graph(); self.update_data_view()

    def get_node_at(self, x, y):
        for nid, (nx, ny) in self.algo.nodes.items():
            if math.hypot(nx-x, ny-y) <= NODE_R: return nid
        return None

    def clear_all(self):
        # [FIX] Truyền đúng tham số để không bị lỗi mất canvas
        self.algo = GraphLogic(canvas=self.canvas, is_directed=self.algo.is_directed)
        self.node_counter = 1
        self.log_text.delete(1.0, tk.END)
        self.draw_graph(); self.update_data_view()
        self.log("Đã Reset.")

    # --- DRAW & ANIM ---
    def draw_edge(self, x1, y1, x2, y2, directed=True, color=COLOR_EDGE, width=2):
        dx = x2 - x1; dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        ox = dx / dist * NODE_R; oy = dy / dist * NODE_R
        
        # --- SỬA DÒNG DƯỚI ĐÂY ---
        arrow_val = tk.LAST if directed else tk.NONE
        
        self.canvas.create_line(
            x1+ox, y1+oy, x2-ox, y2-oy, 
            fill=color, width=width, 
            arrow=arrow_val, # type: ignore
            arrowshape=(12,15,5)
        )

    def draw_graph(self, highlight_nodes=None, highlight_edges=None, path_nodes=None, colors=None):
        self.canvas.delete("all")
        h_nodes = highlight_nodes or []; h_edges = highlight_edges or []; p_nodes = path_nodes or []; cols = colors or {}
        
        # Update mode label
        txt = "CHẾ ĐỘ: CÓ HƯỚNG" if self.algo.is_directed else "CHẾ ĐỘ: VÔ HƯỚNG"
        self.lbl_mode.config(text=txt)

        processed = set()
        for u in self.algo.adj:
            for v, w in self.algo.adj[u].items():
                key = (u,v) if self.algo.is_directed else tuple(sorted((u,v)))
                if key in processed: continue
                processed.add(key)
                if u in self.algo.nodes and v in self.algo.nodes:
                    x1, y1 = self.algo.nodes[u]; x2, y2 = self.algo.nodes[v]
                    width = 4 if (u,v) in h_edges or (v,u) in h_edges else 2
                    self.draw_edge(x1, y1, x2, y2, self.algo.is_directed, COLOR_EDGE, width)
                    mx, my = (x1+x2)/2, (y1+y2)/2
                    # Vẽ cái nền đen che dây đi cho số nó nổi
                    bg = 8
                    self.canvas.create_rectangle(mx-bg, my-bg, mx+bg, my+bg, fill=COLOR_BG, outline="")
                    # Vẽ số lên trên
                    self.canvas.create_text(mx, my, text=str(w), fill="#38c6e6", font=("Arial", 12, "bold"))

        for nid, (x, y) in self.algo.nodes.items():
            fill = cols.get(nid, COLOR_NODE)
            if nid in p_nodes: fill = COLOR_PATH
            elif nid in h_nodes: fill = COLOR_HIGHLIGHT
            outline = COLOR_HIGHLIGHT if nid == self.edge_start else "white"
            self.canvas.create_oval(x-NODE_R, y-NODE_R, x+NODE_R, y+NODE_R, fill=fill, outline=outline, width=2)
            self.canvas.create_text(x, y, text=nid, fill="white", font=("Arial", 10, "bold"))

    # --- HELPER: Hộp thoại nhập Node an toàn ---
    def ask_node(self, title, prompt):
        # Lấy danh sách node hiện có để gợi ý hoặc check
        if not self.algo.nodes: return None
        default_val = list(self.algo.nodes.keys())[0]
        
        while True:
            val = simpledialog.askstring(title, prompt, initialvalue=default_val)
            if val is None: return None # User bấm Cancel
            val = val.strip()
            if val in self.algo.nodes:
                return val
            else:
                messagebox.showerror("Lỗi", f"Node '{val}' không tồn tại! Nhập lại đi.")

    def run_algo(self, name):
        if not self.algo.nodes: 
            messagebox.showwarning("!", "Graph trống trơn, vẽ gì đi bro!"); return
        
        # Reset Log
        self.tabs.select(self.tab_logs)
        self.log_text.delete(1.0, tk.END)
        self.log(f"--- PREPARE: {name.upper()} ---")

        start_node = None
        end_node = None

        # 1. NHÓM CẦN START & END
        if name in ['dijkstra', 'ford']:
            start_node = self.ask_node("Input", f"Chọn Node BẮT ĐẦU cho {name}:")
            if not start_node: return 
            end_node = self.ask_node("Input", f"Chọn Node KẾT THÚC cho {name}:")
            if not end_node: return

        # 2. NHÓM CẦN START ONLY
        elif name in ['bfs', 'dfs', 'prim', 'fleury', 'hierholzer']:
            start_node = self.ask_node("Input", f"Chọn Node BẮT ĐẦU cho {name}:")
            if not start_node: return

        # 3. NHÓM TỰ ĐỘNG (Kruskal, Bipartite) -> Không cần hỏi gì cả

        # --- CHẠY THUẬT TOÁN ---
        self.log(f">> Running {name} | Start={start_node} | End={end_node}")
        
        steps = []; final_colors = None
        try:
            if name == 'bfs': steps = self.algo.bfs(start_node)
            elif name == 'dfs': steps = self.algo.dfs(start_node)
            elif name == 'dijkstra': steps = self.algo.dijkstra(start_node, end_node)
            elif name == 'prim': 
                # Prim cần trick một chút để đảm bảo nó bắt đầu từ đúng node user chọn
                # Logic cũ của Prim tự lấy node[0], giờ ta sửa lại logic gọi hàm hoặc
                # Sửa nhanh: Swap node chọn lên đầu danh sách (hơi phèn)
                # Cách chuẩn: Sửa hàm Prim bên logic nhận tham số start. 
                # -> Ở đây tôi giả định bạn sẽ sửa thêm hàm Prim bên kia nhận tham số start.
                # Nếu không sửa bên kia thì nó sẽ mặc định lấy node đầu tiên.
                # Để triệt để, bạn nên sửa def prim(self, start_node=None) bên logic nhé.
                # Tạm thời gọi thế này nếu logic chưa sửa:
                steps = self.algo.prim(start_node)
                # (Lưu ý: Bạn nên vào prim bên logic sửa dòng 'start = ...' thành 'start = start_node if start_node else ...')

            elif name == 'kruskal': steps = self.algo.kruskal()
            elif name == 'ford': steps = self.algo.ford_fulkerson(start_node, end_node)
            
            elif name == 'bipartite':
                res, steps, final_colors = self.algo.check_bipartite()
                steps.append({'type': 'info', 'desc': "KẾT QUẢ: 2 Phía OK" if res else "KẾT QUẢ: KHÔNG PHẢI 2 PHÍA"})
            
            elif name == 'fleury': 
                # Fleury cũng nên nhận start node nếu muốn chuẩn chỉ
                steps = self.algo.fleury(start_node) 
            elif name == 'hierholzer': 
                steps = self.algo.hierholzer(start_node)

        except Exception as e: 
            self.log(f"Crash: {e}")
            import traceback; traceback.print_exc() # In lỗi ra console để debug
            return
            
        self.animate(steps, final_colors)

    def animate(self, steps, final_colors=None):
        self.step_idx = 0; self.anim_steps = steps; self.final_colors = final_colors
        self.is_animating = True; self.anim_visited = set()
        self._next_step()

    def _next_step(self):
        if not self.is_animating: return
        if self.step_idx >= len(self.anim_steps):
            if self.final_colors: self.draw_graph(colors=self.final_colors)
            self.log("DONE."); self.is_animating = False; return
        
        step = self.anim_steps[self.step_idx]; self.step_idx += 1
        if step.get('desc'): self.log(step['desc'])
        
        typ = step['type']
        h_edges = []; cols = {}
        if typ in ['highlight', 'current']:
            n = step.get('node') or (step.get('nodes')[0] if step.get('nodes') else None)
            if n: self.anim_visited.add(n)
        elif typ in ['traverse']:
            h_edges.append((step['u'], step['v'])); self.anim_visited.add(step['v'])
        elif typ == 'color': cols[step['node']] = COLOR_MAP_BIPARTITE[step['color']]
        elif typ == 'path':
            self.draw_graph(path_nodes=step['nodes']); self.log(f"Path: {'->'.join(step['nodes'])}")
            self.is_animating = False; return

        self.draw_graph(highlight_nodes=list(self.anim_visited), highlight_edges=h_edges, colors=cols)
        self.root.after(600, self._next_step)

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()