from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'system'
app.config['MYSQL_DB'] = 'user_db'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/appointment')
def appointment():
    return render_template('appointment.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[6], password):  # Ensure this matches the correct password field
            session['username'] = username
            session['role'] = user[7]  # Assuming role is stored in the 7th index
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (first_name, last_name, mobile_number, email, username, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (first_name, last_name, mobile_number, email, username, password, 'student'))  # Set role as student
            mysql.connection.commit()
            flash('Registration successful! Welcome, {}!'.format(first_name), 'success')
            return render_template('redirect.html', redirect_url=url_for('login'), delay=10)  # Redirect after 10 seconds
        except Exception as e:
            mysql.connection.rollback()
            flash('Registration failed. Please try again.', 'danger')
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/user/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        flash('Please log in to view the dashboard.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    
    # Get the user details and appointments
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", [username])
    user_id = cur.fetchone()[0]
    
    # Fetch appointments
    cur.execute("SELECT a.id, d.name, a.appointment_date, a.status FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE a.user_id = %s", [user_id])
    appointments = cur.fetchall()
    
    # Fetch bills
    cur.execute("SELECT b.id, b.amount, b.bill_date, a.appointment_date FROM bills b JOIN appointments a ON b.appointment_id = a.id WHERE a.user_id = %s", [user_id])
    bills = cur.fetchall()
    
    # Fetch available doctors
    cur.execute("SELECT id, name, specialty FROM doctors WHERE availability = 'available'")
    doctors = cur.fetchall()
    cur.close()
    
    return render_template('user_dashboard.html', username=username, appointments=appointments, bills=bills, doctors=doctors)


# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
            admin = cur.fetchone()
            if admin and check_password_hash(admin[2], password):  # Assuming password is at index 2
                session['admin_username'] = username
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        except Exception as e:
            flash(f'Error logging in: {str(e)}', 'danger')
        finally:
            cur.close()

    return render_template('admin_login.html')

# Route to Admin Dashboard
# Admin Dashboard: Fetch pending appointments with patient name and appointment time
@app.route('/admin/dashboard')
def admin_dashboard():
    cur = mysql.connection.cursor()
    
    # Fetch all doctors
    cur.execute("SELECT * FROM doctors")
    doctors = cur.fetchall()
    
    # Fetch pending appointments with patient name
    cur.execute("""
        SELECT a.id, u.first_name, u.last_name, a.appointment_date, a.status
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        WHERE a.status = 'pending'
    """)
    appointments = cur.fetchall()
    
    cur.close()

    return render_template('admin_dashboard.html', doctors=doctors, appointments=appointments)


# Route to Add a Doctor
@app.route('/admin/add_doctor', methods=['POST'])
def add_doctor():
    name = request.form['name']
    specialty = request.form['specialty']
    contact = request.form['contact']

    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO doctors (name, specialty, contact) VALUES (%s, %s, %s)", (name, specialty, contact))
        mysql.connection.commit()
        flash('Doctor added successfully!', 'success')
    except Exception as e:
        flash('Error adding doctor: ' + str(e), 'danger')
        mysql.connection.rollback()
    finally:
        cur.close()

    return redirect(url_for('admin_dashboard'))

# Route to Update Doctor Availability
@app.route('/user/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'username' not in session:
        flash('Please log in to book an appointment.', 'warning')
        return redirect(url_for('login'))

    # Fetch available doctors
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM doctors WHERE availability = 'available'")
    doctors = cur.fetchall()
    cur.close()

    # Debug: Print fetched doctors
    print(f"Found {len(doctors)} available doctors: {doctors}")  # Check output

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        username = session['username']

        # Insert the appointment into the appointments table
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO appointments (user_id, doctor_id, appointment_date, status)
                VALUES ((SELECT id FROM users WHERE username = %s), %s, %s, 'pending')
            """, [username, doctor_id, appointment_date])
            mysql.connection.commit()
            flash('Appointment booked successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error booking appointment: {str(e)}', 'danger')
        finally:
            cur.close()

        return redirect(url_for('dashboard'))

    return render_template('user_dashboard.html', doctors=doctors)

@app.route('/admin/update_availability', methods=['POST'])
def update_availability():
    doctor_id = request.form['doctor_id']
    availability = request.form['availability']

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            UPDATE doctors 
            SET availability = %s 
            WHERE id = %s
        """, (availability, doctor_id))
        mysql.connection.commit()
        flash('Doctor availability updated successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error updating availability: {str(e)}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_bill/<appointment_id>', methods=['POST'])
def generate_bill(appointment_id):
    # Logic to generate a bill for a specific appointment
    cur = mysql.connection.cursor()

    # Fetch appointment details
    cur.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
    appointment = cur.fetchone()

    # Generate the bill
    if appointment:
        # Get the bill amount and status from the form
        amount = request.form.get('amount')
        status = request.form.get('status')  # Get the status from the form

        # Insert bill into the 'bills' table
        cur.execute("""
            INSERT INTO bills (appointment_id, amount, bill_date)
            VALUES (%s, %s, NOW())
        """, (appointment_id, amount))  # Use the dynamic amount from the form
        mysql.connection.commit()

        # Update the appointment status to 'Completed'
        cur.execute("""
            UPDATE appointments
            SET status = %s
            WHERE id = %s
        """, (status, appointment_id))  # Update status to 'Completed'
        mysql.connection.commit()

        flash('Bill generated successfully, and appointment status updated!', 'success')
    else:
        flash('Appointment not found!', 'danger')

    cur.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/view_reports', methods=['GET'])
def view_reports():
    search_query = request.args.get('search_query', '')
    page = int(request.args.get('page', 1))

    # Define pagination settings
    items_per_page = 10
    offset = (page - 1) * items_per_page

    # Build query based on search
    query = "SELECT id, amount, bill_date FROM bills WHERE appointment_id LIKE %s OR amount LIKE %s LIMIT %s OFFSET %s"
    params = ('%' + search_query + '%', '%' + search_query + '%', items_per_page, offset)

    cur = mysql.connection.cursor()
    cur.execute(query, params)
    bills = cur.fetchall()

    # Get total count for pagination
    cur.execute("SELECT COUNT(*) FROM bills WHERE appointment_id LIKE %s OR amount LIKE %s", params[:2])
    total_count = cur.fetchone()[0]

    # Calculate total pages
    total_pages = (total_count // items_per_page) + (1 if total_count % items_per_page > 0 else 0)

    cur.close()

    return render_template('view_reports.html', bills=bills, current_page=page, total_pages=total_pages)


@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

