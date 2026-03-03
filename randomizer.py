import random

def parse_labels(raw_text):
    items = []
    for line in raw_text.splitlines():
        for cell in line.replace(',', ' ').split('\t'):
            cell = cell.strip()
            if not cell:
                continue
            
            # split into space separated tokens
            tokens = cell.split()
            i = 0
            while i < len(tokens):
                # check if this token and next two form a range (e.g. NC-1 to NC-5)
                if i + 2 < len(tokens) and tokens[i+1].lower() in ("to", "-"):
                    expanded = expand_range(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")
                    if expanded:
                        items.extend(expanded)
                        i += 3
                        continue
                # otherwise treat as a single label
                if tokens[i].lower() not in ("to", "-"):
                    items.append(tokens[i])
                i += 1
    return items

def expand_range(token):
    if " to " in token:
        start, end = token.split(" to ")
    elif " - " in token:
        start, end = token.split(" - ")
    else:
        return None
    
    # extract prefix and number from start
    i = len(start)
    while i > 0 and start[i-1].isdigit():
        i -= 1
    start_prefix = start[:i]
    start_num = int(start[i:])
    
    # extract prefix and number from end
    j = len(end)
    while j > 0 and end[j-1].isdigit():
        j -= 1
    end_prefix = end[:j]
    end_num = int(end[j:])
    
    # make sure both sides share the same prefix
    if start_prefix != end_prefix:
        return None
    
    # generate every label in between
    return [f"{start_prefix}{n}" for n in range(start_num, end_num + 1)]

def shuffle(items):
    result = items.copy()
    random.shuffle(result)
    return result

def spread_evenly(total, num_slots):
    slots = []
    for i in range(num_slots):
        count = (total * (i + 1)) // num_slots - (total * i) // num_slots
        slots.append(count)
    return slots

def validate(ncs, pcs):
    if len(ncs) == 0:
        return "Please paste at least one NC label."
    if len(ncs) == 1 and len(pcs) > 0:
        return "Need more than 1 NC to place PCs between them."
    return None

def build_sequence(ncs, pcs):
    shuffled_pcs = shuffle(pcs)
    gaps = len(ncs) - 1

    if gaps == 0:
        return [{"label": nc, "type": "NC"} for nc in ncs]

    slots = shuffle(spread_evenly(len(shuffled_pcs), gaps))

    sequence = []
    pc_index = 0

    for i, nc_label in enumerate(ncs):
        sequence.append({"label": nc_label, "type": "NC"})
        if i < gaps:
            for _ in range(slots[i]):
                sequence.append({"label": shuffled_pcs[pc_index], "type": "PC"})
                pc_index += 1

    return sequence

if __name__ == "__main__":
    nc_text = "NC-1 NC-2 NC-3"
    pc_text = "PC-A\nPC-B\nPC-C\nPC-D\nPC-E\nPC-F"

    ncs = parse_labels(nc_text)
    pcs = parse_labels(pc_text)

    print("NCs:", ncs)
    print("PCs:", pcs)

    error = validate(ncs, pcs)
    if error:
        print("Error:", error)
    else:
        sequence = build_sequence(ncs, pcs)
        for i, item in enumerate(sequence):
            print(f"{i+1}. {item['label']}  ({item['type']})")



