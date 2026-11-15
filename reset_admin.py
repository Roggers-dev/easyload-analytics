import sqlite3
import hashlib

def reset_admin_password(new_password):
    # Hash the new password using SHA-256
    hashed_pass = hashlib.sha256(new_password.encode()).hexdigest()
    
    conn = sqlite3.connect('voices_enterprise.db')
    cursor = conn.cursor()
    
    # Update the admin user password
    cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hashed_pass,))
    conn.commit()
    conn.close()
    print("✅ Admin password successfully updated and securely hashed!")

if __name__ == "__main__":
    # Change 'YourNewSecurePassword123!' to your desired password
    reset_admin_password("YourNewSecurePassword123!")