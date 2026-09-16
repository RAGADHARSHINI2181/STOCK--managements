from flask import Flask, request, jsonify, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = "stock.db"

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stock Management System</title>

<style>
* {
    box-sizing: border-box;
    font-family: Arial, sans-serif;
}

body {
    margin: 0;
    padding: 30px;
    background: #f4f6f8;
}

.container {
    max-width: 1100px;
    margin: auto;
    background: white;
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 3px 15px #0002;
}

h1 {
    text-align: center;
    margin-bottom: 25px;
}

.form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}

input {
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 15px;
}

button {
    padding: 11px 16px;
    border: 0;
    border-radius: 6px;
    color: white;
    cursor: pointer;
}

#saveBtn {
    grid-column: 1 / -1;
    background: #087ff5;
}

#cancelBtn {
    grid-column: 1 / -1;
    background: #6c757d;
    display: none;
}

.search {
    width: 100%;
    margin: 25px 0 15px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 11px;
    border: 1px solid #ddd;
    text-align: center;
}

th {
    background: #087ff5;
    color: white;
}

.edit {
    background: #28a745;
    margin-right: 5px;
}

.delete {
    background: #dc3545;
}

#message {
    display: none;
    padding: 10px;
    margin-bottom: 15px;
    border-radius: 6px;
}

@media(max-width:700px) {
    body {
        padding: 10px;
    }

    .form {
        grid-template-columns: 1fr;
    }

    table {
        font-size: 12px;
    }

    th, td {
        padding: 7px;
    }
}
</style>
</head>

<body>

<div class="container">

<h1>Stock Management System</h1>

<div id="message"></div>

<div class="form">

<input id="name" placeholder="Item Name">

<input id="category" placeholder="Category">

<input id="quantity"
       type="number"
       min="0"
       placeholder="Quantity">

<input id="price"
       type="number"
       min="0"
       step="0.01"
       placeholder="Price">

<input id="supplier"
       placeholder="Supplier">

<button id="saveBtn" onclick="saveItem()">
Add Item
</button>

<button id="cancelBtn" onclick="cancelEdit()">
Cancel
</button>

</div>

<input
    class="search"
    id="search"
    placeholder="Search by item, category or supplier..."
    oninput="loadItems()"
>

<table>

<thead>

<tr>
<th>ID</th>
<th>Item Name</th>
<th>Category</th>
<th>Quantity</th>
<th>Price</th>
<th>Supplier</th>
<th>Actions</th>
</tr>

</thead>

<tbody id="tableBody"></tbody>

</table>

</div>


<script>

let editId = null;


function message(text, ok = true) {

    const m = document.getElementById("message");

    m.textContent = text;

    m.style.display = "block";

    m.style.background = ok ? "#d4edda" : "#f8d7da";

    m.style.color = ok ? "#155724" : "#721c24";

    setTimeout(() => {
        m.style.display = "none";
    }, 2500);
}


function clearForm() {

    document.getElementById("name").value = "";

    document.getElementById("category").value = "";

    document.getElementById("quantity").value = "";

    document.getElementById("price").value = "";

    document.getElementById("supplier").value = "";

    editId = null;

    document.getElementById("saveBtn").textContent = "Add Item";

    document.getElementById("saveBtn").style.background = "#087ff5";

    document.getElementById("cancelBtn").style.display = "none";
}


async function loadItems() {

    const q = document.getElementById("search").value;

    const res = await fetch(
        "/api/items?search=" + encodeURIComponent(q)
    );

    const items = await res.json();

    const body = document.getElementById("tableBody");

    body.innerHTML = "";

    if (items.length === 0) {

        body.innerHTML =
            '<tr><td colspan="7">No stock items found</td></tr>';

        return;
    }

    items.forEach(item => {

        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${item.id}</td>

            <td>${escapeHtml(item.name)}</td>

            <td>${escapeHtml(item.category)}</td>

            <td>${item.quantity}</td>

            <td>₹${Number(item.price).toFixed(2)}</td>

            <td>${escapeHtml(item.supplier)}</td>

            <td>

                <button
                    class="edit"
                    onclick="editItem(${item.id})">
                    Edit
                </button>

                <button
                    class="delete"
                    onclick="deleteItem(${item.id})">
                    Delete
                </button>

            </td>
        `;

        body.appendChild(tr);
    });
}


function escapeHtml(value) {

    return String(value).replace(
        /[&<>"']/g,
        c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[c])
    );
}


async function saveItem() {

    const name =
        document.getElementById("name").value.trim();

    const category =
        document.getElementById("category").value.trim();

    const quantity =
        document.getElementById("quantity").value;

    const price =
        document.getElementById("price").value;

    const supplier =
        document.getElementById("supplier").value.trim();


    if (
        !name ||
        !category ||
        quantity === "" ||
        price === "" ||
        !supplier
    ) {

        message("Please fill all fields.", false);

        return;
    }


    if (
        Number(quantity) < 0 ||
        Number(price) < 0
    ) {

        message(
            "Quantity and price cannot be negative.",
            false
        );

        return;
    }


    const data = {

        name: name,

        category: category,

        quantity: Number(quantity),

        price: Number(price),

        supplier: supplier

    };


    const url =
        editId === null
        ? "/api/items"
        : "/api/items/" + editId;


    const method =
        editId === null
        ? "POST"
        : "PUT";


    const res = await fetch(url, {

        method: method,

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(data)

    });


    const result = await res.json();


    if (!res.ok) {

        message(
            result.error || "Operation failed.",
            false
        );

        return;
    }


    if (editId === null) {

        message("Item added successfully!");

    } else {

        message("Item updated successfully!");

    }


    clearForm();

    loadItems();
}


async function editItem(id) {

    const res =
        await fetch("/api/items/" + id);

    const item =
        await res.json();


    if (!res.ok) {

        message(item.error, false);

        return;
    }


    document.getElementById("name").value =
        item.name;

    document.getElementById("category").value =
        item.category;

    document.getElementById("quantity").value =
        item.quantity;

    document.getElementById("price").value =
        item.price;

    document.getElementById("supplier").value =
        item.supplier;


    editId = id;


    document.getElementById("saveBtn")
        .textContent = "Update Item";


    document.getElementById("saveBtn")
        .style.background = "#28a745";


    document.getElementById("cancelBtn")
        .style.display = "block";


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


async function deleteItem(id) {

    if (
        !confirm(
            "Are you sure you want to delete this item?"
        )
    ) {
        return;
    }


    const res =
        await fetch(
            "/api/items/" + id,
            {
                method: "DELETE"
            }
        );


    const result =
        await res.json();


    if (!res.ok) {

        message(
            result.error || "Delete failed.",
            false
        );

        return;
    }


    message("Item deleted successfully!");

    loadItems();
}


function cancelEdit() {

    clearForm();

}


loadItems();

</script>

</body>
</html>
"""


# ============================================================
# DATABASE
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            quantity INTEGER NOT NULL
                CHECK(quantity >= 0),

            price REAL NOT NULL
                CHECK(price >= 0),

            supplier TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()


# ============================================================
# VALIDATION
# ============================================================

def validate_data(data):

    name = str(
        data.get("name", "")
    ).strip()


    category = str(
        data.get("category", "")
    ).strip()


    supplier = str(
        data.get("supplier", "")
    ).strip()


    if not name or not category or not supplier:

        return None, "All fields are required."


    try:

        quantity = int(
            data.get("quantity")
        )

        price = float(
            data.get("price")
        )

    except (TypeError, ValueError):

        return None, (
            "Quantity must be an integer "
            "and price must be a number."
        )


    if quantity < 0 or price < 0:

        return None, (
            "Quantity and price cannot be negative."
        )


    return {

        "name": name,

        "category": category,

        "quantity": quantity,

        "price": price,

        "supplier": supplier

    }, None


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ============================================================
# CREATE + READ ALL
# ============================================================

@app.route("/api/items", methods=["GET", "POST"])
def items():

    # CREATE
    if request.method == "POST":

        data, error = validate_data(
            request.get_json(silent=True) or {}
        )


        if error:

            return jsonify({
                "error": error
            }), 400


        conn = get_db()


        cursor = conn.execute("""

            INSERT INTO items
            (
                name,
                category,
                quantity,
                price,
                supplier
            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            data["name"],

            data["category"],

            data["quantity"],

            data["price"],

            data["supplier"]

        ))


        conn.commit()


        item_id = cursor.lastrowid


        conn.close()


        return jsonify({

            "message":
                "Item created successfully",

            "id":
                item_id

        }), 201


    # READ ALL

    search = request.args.get(
        "search", ""
    ).strip()


    conn = get_db()


    if search:

        pattern = "%" + search + "%"


        rows = conn.execute("""

            SELECT *
            FROM items

            WHERE name LIKE ?
            OR category LIKE ?
            OR supplier LIKE ?

            ORDER BY id DESC

        """, (

            pattern,
            pattern,
            pattern

        )).fetchall()


    else:

        rows = conn.execute("""

            SELECT *
            FROM items

            ORDER BY id DESC

        """).fetchall()


    conn.close()


    return jsonify([
        dict(row)
        for row in rows
    ])


# ============================================================
# READ ONE + UPDATE + DELETE
# ============================================================

@app.route(
    "/api/items/<int:item_id>",
    methods=["GET", "PUT", "DELETE"]
)
def item(item_id):

    conn = get_db()


    # READ ONE

    if request.method == "GET":

        row = conn.execute("""

            SELECT *
            FROM items
            WHERE id = ?

        """, (item_id,)).fetchone()


        conn.close()


        if row is None:

            return jsonify({
                "error": "Item not found."
            }), 404


        return jsonify(dict(row))


    # UPDATE

    if request.method == "PUT":

        data, error = validate_data(
            request.get_json(silent=True) or {}
        )


        if error:

            conn.close()

            return jsonify({
                "error": error
            }), 400


        cursor = conn.execute("""

            UPDATE items

            SET
                name = ?,
                category = ?,
                quantity = ?,
                price = ?,
                supplier = ?

            WHERE id = ?

        """, (

            data["name"],

            data["category"],

            data["quantity"],

            data["price"],

            data["supplier"],

            item_id

        ))


        conn.commit()


        if cursor.rowcount == 0:

            conn.close()

            return jsonify({
                "error": "Item not found."
            }), 404


        conn.close()


        return jsonify({

            "message":
                "Item updated successfully"

        })


    # DELETE

    cursor = conn.execute("""

        DELETE FROM items
        WHERE id = ?

    """, (item_id,))


    conn.commit()


    if cursor.rowcount == 0:

        conn.close()

        return jsonify({
            "error": "Item not found."
        }), 404


    conn.close()


    return jsonify({

        "message":
            "Item deleted successfully"

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    init_db()

    print()
    print("======================================")
    print("     STOCK MANAGEMENT SYSTEM")
    print("======================================")
    print("Database : stock.db")
    print("Website  : http://127.0.0.1:5000")
    print("======================================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )