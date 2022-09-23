
class node:
    def __init__(self, val):
        self.val = val
        self.right = None
        self.left = None
    
    def insert(self, val):
        if val > self.val:
            if self.right is not None:
                self.right.insert(val)
            else:
                self.right = node(val)
        if val < self.val:
            if self.left is not None:
                self.left.insert(val)
            else:
                self.left = node(val)
    

def print_tree(root):
    queue = [root]
    while queue:
        curr = queue.pop(0)
        if curr.left:
            queue.append(curr.left)
        if curr.right:
            queue.append(curr.right)
        print(curr.val)

root = node(5)
root.insert(1)
root.insert(7)
root.insert(6)
root.insert(14)
root.insert(2)

print_tree(root)