
class Checker:
    def __init__(self, name):
        self.name = name
        self.passed = 0
        self.failed = []
    def check(self, label, cond, detail=""):
        if cond:
            self.passed += 1
        else:
            self.failed.append(f"{label}: {detail}")
        return cond
    def eq(self, label, got, want):
        return self.check(label, got == want, f"got={got} want={want}")
    def report(self):
        total = self.passed + len(self.failed)
        print(f"{self.name:12s} {'PASS' if not self.failed else 'FAIL'}  pass={self.passed} fail={len(self.failed)} total={total}")
        for f in self.failed:
            print("   -", f)
        return not self.failed
