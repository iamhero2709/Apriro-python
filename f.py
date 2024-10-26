from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import csv
from collections import defaultdict
from itertools import combinations

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/apriori', methods=['POST'])
def apriori_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    min_sup = request.form.get('min_sup', type=int)

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if min_sup is None:
        return jsonify({'error': 'Minimum support is missing'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Read data from the uploaded file
    D = read_data(file_path)
    # Run the Apriori algorithm
    L = apriori(D, min_sup)

    # Prepare response
    frequent_itemsets = [list(itemset) for itemset in L]
    response = {
        'min_sup': min_sup,
        'frequent_itemsets': frequent_itemsets
    }
    return jsonify(response)


def read_data(input_file):
    D = []
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            transaction = set(row)
            D.append(transaction)
    return D


def find_frequent_1_itemsets(D, min_sup):
    item_counts = defaultdict(int)
    for transaction in D:
        for item in transaction:
            item_counts[frozenset([item])] += 1

    L1 = {itemset for itemset, count in item_counts.items() if count >= min_sup}
    return L1


def apriori_gen(Lk_minus_1):
    Ck = set()
    Lk_minus_1_list = list(Lk_minus_1)
    len_Lk_minus_1 = len(Lk_minus_1_list)

    for i in range(len_Lk_minus_1):
        for j in range(i+1, len_Lk_minus_1):
            l1 = list(Lk_minus_1_list[i])
            l2 = list(Lk_minus_1_list[j])
            l1.sort()
            l2.sort()

            if l1[:-1] == l2[:-1]:
                candidate = frozenset(l1 + [l2[-1]])
                if has_infrequent_subset(candidate, Lk_minus_1):
                    continue
                Ck.add(candidate)
    return Ck


def has_infrequent_subset(candidate, Lk_minus_1):
    k = len(candidate)
    subsets = combinations(candidate, k - 1)
    for subset in subsets:
        if frozenset(subset) not in Lk_minus_1:
            return True
    return False


def apriori(D, min_sup):
    L1 = find_frequent_1_itemsets(D, min_sup)
    L = [L1]
    k = 2

    while True:
        Ck = apriori_gen(L[k-2])

        item_counts = defaultdict(int)
        for transaction in D:
            transaction_items = frozenset(transaction)
            for candidate in Ck:
                if candidate.issubset(transaction_items):
                    item_counts[candidate] += 1

        Lk = {itemset for itemset, count in item_counts.items() if count >= min_sup}

        if not Lk:
            break

        L.append(Lk)
        k += 1

    frequent_itemsets = set().union(*L)
    maximal_itemsets = remove_nonmaximal(frequent_itemsets)
    return maximal_itemsets


def remove_nonmaximal(frequent_itemsets):
    maximal_itemsets = set()
    for itemset in frequent_itemsets:
        is_maximal = True
        for other_itemset in frequent_itemsets:
            if itemset != other_itemset and itemset.issubset(other_itemset):
                is_maximal = False
                break
        if is_maximal:
            maximal_itemsets.add(itemset)
    return maximal_itemsets


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
