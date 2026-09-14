"""Parser de instancias GQMKP (formato GAMS .inc) + evaluador/verificador exacto (float64).

Convenciones (identicas al codigo HESA):
- Items j=0..n-1, mochilas k=0..m-1, k=m es la mochila ficticia (no asignado).
- p_jk = po_j * psi[clase(j)][k]  (perfil de mochila)
- Objetivo f = sum_j p[j, sol_j] + sum_{i<j, sol_i==sol_j<m} q_ij
- Restr. capacidad: sum_{j en k} w_j + sum_{clases r presentes en k} s_r <= c
- Restr. clase: la clase r aparece en a lo sumo n_r mochilas reales.
"""
import re
import numpy as np
from pathlib import Path


class Instance:
    __slots__ = ("name", "n", "m", "h", "w", "po", "q", "t_jr", "s", "nr", "psi", "cap", "p")

    def feasible(self, sol, tol=1e-8):
        """sol: array de n con valores 0..m (m = no asignado). Devuelve (ok, msg)."""
        sol = np.asarray(sol)
        for k in range(self.m):
            items = np.where(sol == k)[0]
            classes = set(self.t_jr[j] for j in items)
            load = self.w[items].sum() + sum(self.s[r] for r in classes)
            if load > self.cap + tol:
                return False, f"capacidad excedida en mochila {k}: {load} > {self.cap}"
        for r in range(self.h):
            ks = set(sol[j] for j in range(self.n) if self.t_jr[j] == r and sol[j] < self.m)
            if len(ks) > self.nr[r]:
                return False, f"clase {r} en {len(ks)} mochilas > nr={self.nr[r]}"
        return True, "ok"

    def objective(self, sol):
        sol = np.asarray(sol)
        f = 0.0
        alloc = sol < self.m
        f += self.p[np.arange(self.n)[alloc], sol[alloc]].sum()
        for k in range(self.m):
            items = np.where(sol == k)[0]
            if len(items) > 1:
                sub = self.q[np.ix_(items, items)]
                f += np.triu(sub, 1).sum()
        return float(f)


def parse_instance(path):
    text = Path(path).read_text()
    ins = Instance()
    ins.name = Path(path).stem

    ins.n = int(re.search(r"j\s+siparis turu\s*/1\*(\d+)/", text).group(1))
    ins.m = int(re.search(r"k\s+knapsack indisi\s*/1\*(\d+)/", text).group(1))
    ins.h = int(re.search(r"r\s+kalip indisi\s*/1\*(\d+)/", text).group(1))

    def block(header_regex):
        mm = re.search(header_regex, text)
        start = mm.end()
        end = text.find("/", start)
        # el bloque termina en "/;" o "/ ;" -- busca el primer '/' tras start
        return text[start:end]

    def parse_scalar_block(header_regex):
        body = block(header_regex)
        out = {}
        for line in body.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                out[int(parts[0])] = float(parts[1])
        return out

    def parse_pair_block(header_regex):
        body = block(header_regex)
        out = {}
        for mm in re.finditer(r"(\d+)\.(\d+)\s*=\s*([\d.eE+-]+)", body):
            out[(int(mm.group(1)), int(mm.group(2)))] = float(mm.group(3))
        return out

    wd = parse_scalar_block(r"parameter\s+w\(j\)\s*/")
    ins.w = np.array([wd.get(j + 1, 0.0) for j in range(ins.n)])
    pod = parse_scalar_block(r"parameter\s+po\(j\)\s*/")
    ins.po = np.array([pod.get(j + 1, 0.0) for j in range(ins.n)])

    ins.cap = float(re.search(r"cap\(k\)\s*=\s*([\d.]+)", text).group(1))

    qd = parse_pair_block(r"parameter\s+pp\(i,j\)\s*/")
    ins.q = np.zeros((ins.n, ins.n))
    for (i, j), v in qd.items():
        ins.q[i - 1, j - 1] = v
        ins.q[j - 1, i - 1] = v

    td = parse_pair_block(r"parameter\s+t\(r,j\)\s*/")
    ins.t_jr = np.full(ins.n, -1, dtype=int)
    for (r, j), v in td.items():
        if v:
            ins.t_jr[j - 1] = r - 1
    assert (ins.t_jr >= 0).all(), "item sin clase"

    sd = parse_scalar_block(r"parameter\s+s\(r\)\s*/")
    ins.s = np.array([sd.get(r + 1, 0.0) for r in range(ins.h)])
    nrd = parse_scalar_block(r"parameter\s+nr\(r\)\s*/")
    ins.nr = np.array([int(nrd.get(r + 1, 0)) for r in range(ins.h)], dtype=int)

    psid = parse_pair_block(r"parameter\s+psi\(r,k\)\s*/")
    ins.psi = np.zeros((ins.h, ins.m))
    for (r, k), v in psid.items():
        ins.psi[r - 1, k - 1] = v

    # p_jk = po_j * sum_r t_rj * psi_rk  (t es 0/1 con una clase por item)
    ins.p = ins.po[:, None] * ins.psi[ins.t_jr, :]
    return ins


def load_best_sols(path):
    """Lee best_sol(...).txt -> {nombre_instancia: (f, sol)}. Devuelve la mejor entrada por instancia."""
    lines = Path(path).read_text().strip().splitlines()
    out = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        parts = line.split()
        # linea de cabecera: "<ruta_instancia> <objetivo>"
        if len(parts) == 2 and (parts[0].endswith(".inc") or parts[0].endswith(".txt")) :
            name = Path(parts[0].replace("\\", "/")).stem
            f = float(parts[1])
            sol = np.array([int(x) for x in lines[i + 1].split()])
            if name not in out or f > out[name][0]:
                out[name] = (f, sol)
            i += 2
        else:
            i += 1
    return out


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent.parent / "instances_and_solutions" / "instances_and_solutions"
    inst_root = root / "instances"
    sols = load_best_sols(root / "results" / "best_sol(100Genes).txt")
    print(f"{len(sols)} soluciones certificadas leidas")
    bad = 0
    for name, (f_rep, sol) in sorted(sols.items()):
        cand = list(inst_root.glob(f"*/{name}.inc"))
        if not cand:
            print(f"  {name}: instancia no encontrada, salto")
            continue
        ins = parse_instance(cand[0])
        ok, msg = ins.feasible(sol)
        f_eval = ins.objective(sol)
        status = "OK" if (ok and abs(f_eval - f_rep) < 0.01) else "MISMATCH"
        if status != "OK":
            bad += 1
            print(f"  {name}: {status} feas={ok} ({msg}) f_eval={f_eval:.4f} vs f_rep={f_rep:.4f}")
    print(f"listo, {bad} discrepancias")
