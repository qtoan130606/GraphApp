import heapq
from collections import deque
import math

# Constants
COLOR_MAP_BIPARTITE = {0: "#f44336", 1: "#2196f3"} 

class GraphLogic:
    def __init__(self, canvas=None, is_directed=True):
# canvas: đối tượng giao diện dùng để VẼ ĐỒ THỊ (CƠ BẢN 1)
# GraphLogic chỉ quản lý dữ liệu (nodes, raw_edges, adj) để hỗ trợ vẽ và lưu ( CƠ BẢN 2)
        self.canvas = canvas
        self.nodes = {}      # Lưu tọa độ: {'1': (x, y)}
        self.raw_edges = []  # [CORE] Source of truth: [('1', '2', 4)]
        self.adj = {}        # Danh sách kề dùng để chạy thuật toán
        self.is_directed = is_directed

    # --- QUẢN LÝ DỮ LIỆU & MODE ---
    def set_mode(self, directed_mode):
        """Đổi chế độ và tự động xây lại đồ thị"""
        if self.is_directed == directed_mode: return
        self.is_directed = directed_mode
        self.rebuild_adj() 
    # CƠ BẢN 6: Chuyển lại adj từ raw_edges (danh sách cạnh -> danh sách kề)
    def rebuild_adj(self):
        """Xóa sạch adj cũ, nạp lại từ raw_edges theo chế độ hiện tại"""
        self.adj = {n: {} for n in self.nodes}
        for u, v, w in self.raw_edges:
            self._add_to_adj(u, v, w)

    def add_node(self, nid, x, y):
        nid = str(nid)
        self.nodes[nid] = (x, y)
        if nid not in self.adj: self.adj[nid] = {}

    def add_edge(self, u, v, w=1):
        u, v = str(u), str(v)
        if u not in self.nodes or v not in self.nodes: return
        
        # 1. Update vào raw_edges (Gốc)
        exists = False
        for i, (ru, rv, rw) in enumerate(self.raw_edges):
            if ru == u and rv == v:
                self.raw_edges[i] = (u, v, w) 
                exists = True
                break
        if not exists:
            self.raw_edges.append((u, v, w))

        # 2. Update vào adj (Ngọn)
        self._add_to_adj(u, v, w)

    def _add_to_adj(self, u, v, w):
        if u not in self.adj: self.adj[u] = {}
        self.adj[u][v] = w
        # Nếu Vô Hướng -> Thêm chiều ngược lại
        if not self.is_directed: 
            if v not in self.adj: self.adj[v] = {}
            self.adj[v][u] = w

    def remove_node(self, nid):
        nid = str(nid)
        if nid in self.nodes: del self.nodes[nid]
        if nid in self.adj: del self.adj[nid]
        # Xóa sạch trong raw_edges
        self.raw_edges = [e for e in self.raw_edges if e[0] != nid and e[1] != nid]
        for u in self.adj:
            if nid in list(self.adj[u].keys()): del self.adj[u][nid]

    # CƠ BẢN 6: Lấy ma trận kề từ danh sách kề (adj)
    def get_matrix(self):
        nodes = sorted(list(self.nodes.keys()), key=lambda x: int(x) if x.isdigit() else x)
        n = len(nodes)
        idx = {node: i for i, node in enumerate(nodes)}
        mat = [[0] * n for _ in range(n)]
        for u in self.adj:
            for v, w in self.adj[u].items():
                if u in idx and v in idx: mat[idx[u]][idx[v]] = w
        return nodes, mat
    
    # CƠ BẢN 6: Lấy danh sách cạnh từ danh sách kề (adj)
    def get_edge_list(self):
        edges = []
        processed = set()
        for u in self.adj:
            for v, w in self.adj[u].items():
                key = tuple(sorted((u, v))) if not self.is_directed else (u, v)
                if not self.is_directed and key in processed: continue
                processed.add(key)
                edges.append((u, v, w))
        return edges

    # CƠ BẢN 4: Duyệt đồ thị theo chiến lược BFS 
    def bfs(self, start):
        steps = []
        queue = deque([start])
        visited = {start}
        steps.append({'type': 'highlight', 'nodes': [start], 'desc': f'BFS Start: {start}'})
        while queue:
            u = queue.popleft()
            steps.append({'type': 'current', 'node': u, 'desc': f'Pop {u}'})
            if u in self.adj:
                neighbors = sorted(self.adj[u].keys(), key=lambda x: int(x) if x.isdigit() else x)
                for v in neighbors:
                    if v not in visited:
                        visited.add(v); queue.append(v)
                        steps.append({'type': 'traverse', 'u': u, 'v': v, 'desc': f'Visit {v}'})
        return steps
    
    # CƠ BẢN 4: Duyệt đồ thị theo chiến lược DFS
    def dfs(self, start):
        steps = []; visited = set()
        def _visit(u):
            visited.add(u)
            steps.append({'type': 'highlight', 'nodes':[u], 'desc':f'DFS Visit {u}'})
            neighbors = sorted(self.adj.get(u, {}).keys(), key=lambda x: int(x) if x.isdigit() else x)
            for v in neighbors:
                if v not in visited:
                    steps.append({'type': 'traverse', 'u':u, 'v':v, 'desc':f'Go to {v}'})
                    _visit(v)
        _visit(start)
        return steps

    # CƠ BẢN 3: Thuật toán Dijkstra – Tìm đường đi ngắn nhất giữa 2 đỉnh
    def dijkstra(self, start, end):
        steps = []
        pq = [(0, start)]
        dist = {n: float('inf') for n in self.nodes}
        parent = {start: None}
        dist[start] = 0
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]: continue
            steps.append({'type': 'current', 'node': u, 'desc': f'Xét {u} (min={d})'})
            if u == end: break
            neighbors = sorted(self.adj.get(u, {}).items(), key=lambda item: int(item[0]) if item[0].isdigit() else item[0])
            for v, w in neighbors:
                new_cost = dist[u] + w
                if new_cost < dist[v]:
                    dist[v] = new_cost; parent[v] = u
                    heapq.heappush(pq, (new_cost, v))
                    steps.append({'type': 'relax', 'u': u, 'v': v, 'desc': f'Update {v}={new_cost}'})
        path = []
        if dist[end] != float('inf'):
            curr = end
            while curr is not None: path.append(curr); curr = parent.get(curr)
            path.reverse()
            steps.append({'type': 'path', 'nodes': path, 'desc': f'Shortest Path: {dist[end]}'})
        return steps

    # --- THUẬT TOÁN BỊ CHẶN Ở CHẾ ĐỘ CÓ HƯỚNG ---

    #CƠ BẢN 5: Kiểm tra một đồ thị có phải là đồ thị 2 phía không?
    def check_bipartite(self):
        steps = []
        # [BLOCK] Bipartite Check
        if self.is_directed:
            steps.append({'type': 'info', 'desc': 'LỖI: Kiểm tra 2 phía chỉ dành cho Đồ thị Vô Hướng.'})
            return False, steps, None

        colors = {}
        for start in self.nodes:
            if start not in colors:
                colors[start] = 0
                steps.append({'type': 'color', 'node': start, 'color': 0, 'desc': 'start group A'})
                queue = deque([start])
                while queue:
                    u = queue.popleft()
                    neighbors = sorted(self.adj.get(u, {}).keys(), key=lambda x: int(x) if x.isdigit() else x)
                    for v in neighbors:
                        if v not in colors:
                            colors[v] = 1 - colors[u]
                            steps.append({'type': 'color', 'node': v, 'color': colors[v], 'desc': 'paint'})
                            queue.append(v)
                        elif colors[v] == colors[u]:
                            return False, steps, {nid: COLOR_MAP_BIPARTITE[c] for nid, c in colors.items()}
        return True, steps, {nid: COLOR_MAP_BIPARTITE[c] for nid, c in colors.items()}

    # NÂNG CAO 7.1: Thuật toán PRIM 
    def prim(self): 
        steps = []
        # [BLOCK] Prim MST
        if self.is_directed:
            steps.append({'type': 'info', 'desc': 'LỖI: Prim (MST) chỉ áp dụng cho Đồ thị Vô Hướng.'})
            return steps
            
        if not self.nodes: return steps
        start = list(self.nodes.keys())[0]
        visited = {start}; edges = []
        for v, w in self.adj.get(start, {}).items(): heapq.heappush(edges, (w, start, v))
        steps.append({'type': 'highlight', 'nodes': [start], 'desc': 'Prim Start'})
        while edges:
            w, u, v = heapq.heappop(edges)
            if v in visited: continue
            visited.add(v)
            steps.append({'type': 'traverse', 'u': u, 'v': v, 'desc': f'Add Edge {u}-{v}'})
            for nv, nw in self.adj.get(v, {}).items():
                if nv not in visited: heapq.heappush(edges, (nw, v, nv))
        return steps
    
    #NÂNG CAO 7.2: Thuật toán KRUSKAL
    def kruskal(self): 
        steps = []
        # [BLOCK] Kruskal MST
        if self.is_directed:
            steps.append({'type': 'info', 'desc': 'LỖI: Kruskal (MST) chỉ áp dụng cho Đồ thị Vô Hướng.'})
            return steps

        edges = set()
        for u in self.adj:
            for v, w in self.adj[u].items():
                if u < v: edges.add((w, u, v)) # Chỉ lấy 1 chiều để không trùng
        sorted_edges = sorted(list(edges), key=lambda x: (x[0], x[1], x[2]))
        
        parent = {n: n for n in self.nodes}
        def find(n): return find(parent[n]) if parent[n] != n else n
        def union(n1, n2):
            r1, r2 = find(n1), find(n2)
            if r1 != r2: parent[r1] = r2; return True
            return False
        
        for w, u, v in sorted_edges:
            if union(u, v): steps.append({'type': 'traverse', 'u': u, 'v': v, 'desc': f'Kruskal picks {u}-{v}'})
        return steps

    # NÂNG CAO 7.3: Thuật toán FORD–FULKERSON
    def ford_fulkerson(self, source, sink):
        steps = []
        # Ford-Fulkerson chạy được cả 2, nhưng thường dùng cho Có Hướng.
        # Ở đây KHÔNG CHẶN, để nó chạy bình thường.
        residual = {u: {v: w for v, w in self.adj.get(u, {}).items()} for u in self.adj}
        max_flow = 0
        while True:
            parent = {n: None for n in self.nodes}
            queue = deque([source]); found = False
            while queue:
                u = queue.popleft()
                if u == sink: found = True; break
                for v, cap in residual.get(u, {}).items():
                    if parent[v] is None and cap > 0 and v != source:
                        parent[v] = u; queue.append(v)
            if not found: break 
            path_flow = float('inf'); v = sink; path = [sink]
            while v != source:
                u = parent[v]; path_flow = min(path_flow, residual[u][v]); v = u; path.append(v)
            max_flow += path_flow
            steps.append({'type': 'path', 'nodes': path[::-1], 'desc': f'Flow +{path_flow}'})
            v = sink
            while v != source:
                u = parent[v]; residual[u][v] -= path_flow
                if v not in residual: residual[v] = {}
                if u not in residual[v]: residual[v][u] = 0
                residual[v][u] += path_flow; v = u
            steps.append({'type': 'info', 'desc': f'Max Flow: {max_flow}'})
        return steps

    # NÂNG CAO 7.4: Thuật toán FLEURY 
    def fleury(self):
        steps = []
        # [BLOCK] Fleury
        if self.is_directed:
             steps.append({'type': 'info', 'desc': 'LỖI: Fleury (Euler) chỉ áp dụng cho Đồ thị Vô Hướng.'})
             return steps 
        
        if not self.nodes: return steps
        
        # Logic Vô Hướng
        odd = [u for u in self.adj if len(self.adj[u]) % 2 != 0]
        if len(odd) > 2:
             steps.append({'type': 'info', 'desc': 'LỖI: Không thỏa mãn đk Euler (Số đỉnh bậc lẻ > 2)'})
             return steps
             
        temp_adj = {u: list(v.keys()) for u, v in self.adj.items()} 
        start_node = odd[0] if odd else list(self.nodes.keys())[0]
        curr = start_node; path = [curr]
        steps.append({'type': 'highlight', 'nodes': [curr], 'desc': f'Start Fleury: {curr}'})
        
        while any(temp_adj.values()): 
            neighbors = sorted(temp_adj.get(curr, []), key=lambda x: int(x) if x.isdigit() else x)
            chosen_v = None
            if len(neighbors) == 1: chosen_v = neighbors[0]
            else:
                for v in neighbors:
                    temp_adj[curr].remove(v)
                    if curr in temp_adj.get(v, []): temp_adj[v].remove(curr)
                    # Check cầu
                    def count_reachable(start_n):
                        q = deque([start_n]); seen = {start_n}; cnt = 0
                        while q:
                            c = q.popleft(); cnt+=1
                            for nxt in temp_adj.get(c, []):
                                if nxt not in seen: seen.add(nxt); q.append(nxt)
                        return cnt
                    
                    can_reach_v = False
                    q_chk = deque([curr]); seen_chk = {curr}
                    while q_chk:
                        c_chk = q_chk.popleft()
                        if c_chk == v: can_reach_v = True; break
                        for nxt_chk in temp_adj.get(c_chk, []):
                            if nxt_chk not in seen_chk: seen_chk.add(nxt_chk); q_chk.append(nxt_chk)
                    
                    temp_adj[curr].append(v); temp_adj[v].append(curr)
                    if can_reach_v: chosen_v = v; break
                if chosen_v is None: chosen_v = neighbors[0]
            
            if chosen_v is None: break 
            steps.append({'type': 'traverse', 'u': curr, 'v': chosen_v, 'desc': f'Cross {curr}-{chosen_v}'})
            
            temp_adj[curr].remove(chosen_v)
            if chosen_v in temp_adj and curr in temp_adj[chosen_v]: temp_adj[chosen_v].remove(curr)
            curr = chosen_v; path.append(curr)
        
        steps.append({'type': 'path', 'nodes': path, 'desc': 'Fleury Done'})
        return steps

     # NÂNG CAO 7.5: Thuật toán HIERHOLZER 
    def hierholzer(self):
        steps = []
        # [BLOCK] Hierholzer (Block directed cho an toàn)
        if self.is_directed:
             steps.append({'type': 'info', 'desc': 'LỖI: Thuật toán này hiện chỉ hỗ trợ Đồ thị Vô Hướng.'})
             return steps
             
        if not self.nodes: return steps
        
        # Logic Vô Hướng
        odd = [u for u in self.adj if len(self.adj[u]) % 2 != 0]
        if odd: 
            steps.append({'type': 'info', 'desc': f'LỖI: Không có chu trình Euler (Có {len(odd)} đỉnh bậc lẻ)'})
            return steps
            
        temp_adj = {u: list(v.keys()) for u, v in self.adj.items()}
        start_node = list(self.nodes.keys())[0]
        for n in self.nodes:
             if temp_adj.get(n): start_node = n; break
             
        stack = [start_node]; circuit = []
        steps.append({'type': 'highlight', 'nodes': [start_node], 'desc': f'Hierholzer Start: {start_node}'})
        while stack:
            u = stack[-1]
            if temp_adj.get(u):
                neighbors = sorted(temp_adj[u], key=lambda x: int(x) if x.isdigit() else x)
                v = neighbors[0]
                stack.append(v)
                temp_adj[u].remove(v)
                if v in temp_adj and u in temp_adj[v]: temp_adj[v].remove(u)
                steps.append({'type': 'traverse', 'u': u, 'v': v, 'desc': f'Go {u}->{v}'})
            else:
                node = stack.pop(); circuit.append(node)
                steps.append({'type': 'current', 'node': node, 'desc': f'Backtrack {node}'})
        steps.append({'type': 'path', 'nodes': circuit[::-1], 'desc': 'Euler Circuit Found'})
        return steps

    