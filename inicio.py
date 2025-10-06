from flask import Flask, flash, render_template, request, redirect, url_for, Response, session
from flask_mysqldb import MySQL

app = Flask(__name__) #Creando el objeto aplicación
app.secret_key = 'appsecretkey' #Clave secreta para la sesión
mysql = MySQL() #Inicializando la extensión de MySQL

# conexion de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'R57606795'
app.config['MYSQL_DB'] = 'ventas'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)

# FUNCION DE ACCESO A LOGIN
@app.route('/accesologin', methods=['GET', 'POST'])
def accesologin():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['logueado'] = True
            session['id'] = user['id']
            session['id_rol'] = user['id_rol']
            if user['id_rol'] == 1:
                flash('Bienvenido Administrador', 'success')
                return redirect(url_for('admin'))  # mejor usar redirect
            elif user['id_rol'] == 2:
                return render_template('admin.html')
        else:
            flash('Usuario y contraseña incorrectos', 'danger')
            return render_template('login.html', error='Usuario y contraseña incorrectos')

    # Si no es POST o no se envió email/password
    return redirect(url_for('login'))

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        cursor.execute("""
            UPDATE usuario SET nombre = %s, email = %s, password = %s WHERE id = %s
        """, (nombre, email, password, id))
        mysql.connection.commit()
        cursor.close()
        flash('Usuario actualizado correctamente', 'success')
        return redirect(url_for('usuario'))
    else:
        cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        cursor.close()
        return render_template('editar_usuario.html', usuario=usuario)
    
@app.route('/eliminar_usuario/<int:id>')
def eliminar_usuario(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash('Usuario eliminado correctamente', 'info')
    return redirect(url_for('usuario'))

#FUNCION REGISTRO DE USUARIOS
@app.route('/crearusuario', methods=['GET', 'POST'])
def crearusuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        # Verificar si el correo ya existe
        cursor.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        existe = cursor.fetchone()
        if existe:
            cursor.close()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {'success': False, 'message': 'Este correo ya está registrado'}, 400
            flash('Este correo ya está registrado', 'warning')
            return redirect(url_for('registro'))

        # Insertar nuevo usuario
        cursor.execute("""
            INSERT INTO usuario (nombre, email, password, id_rol)
            VALUES (%s, %s, %s, '2')
        """, (nombre, email, password))
        mysql.connection.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {
                'success': True,
                'message': 'Usuario registrado exitosamente',
                'usuario': {
                    'id': nuevo_id,
                    'nombre': nombre,
                    'email': email,
                    'password': password,
                    'id_rol': 2
                }
            }
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('usuario'))

    return render_template('registro.html')


@app.route('/')
def inicio():
    if 'logueado' in session:
        if session.get('id_rol') == 1:
            return render_template('baseadmin.html')
        elif session.get('id_rol') == 2:
            return render_template('usuario.html')
    return render_template('index.html')

@app.route('/contacto_post', methods=['GET', 'POST'])
def contacto_post():
    user={ #diccionario de contactos
        'nombre':'',
        'email':'',
        'mensaje':''
    }
    if request.method == 'POST':
        user['nombre'] = request.form.get('nombre','')
        user['email'] = request.form.get('email','')
        user['mensaje'] = request.form.get('mensaje','')
    return render_template('contacto_post.html', usuario=user)

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/acercade')
def acercade():
    return render_template('acercade.html')

@app.route('/login')
def login():
    return render_template('login.html')

# Mostrar productos
@app.route('/gestionproducto')
def gestionproducto():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM producto")
    productos = cursor.fetchall()
    cursor.close()
    return render_template('gestionproducto.html', productos=productos)

# Agregar producto
@app.route('/agregar', methods=['POST'])
def agregar():
    try:
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        categoria = request.form['categoria']
        cantidad = int(request.form['cantidad'])
        precio_compra = float(request.form['precio_compra'])
        precio_venta = float(request.form['precio_venta'])
        proveedor = request.form.get('proveedor')
        fecha_compra = request.form.get('fecha_compra')
        fecha_vencimiento = request.form.get('fecha_vencimiento')

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO producto (
                codigo, nombre, categoria, cantidad,
                precio_compra, precio_venta, proveedor,
                fecha_compra, fecha_vencimiento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (codigo, nombre, categoria, cantidad,
              precio_compra, precio_venta, proveedor,
              fecha_compra, fecha_vencimiento))
        mysql.connection.commit()
        cursor.close()

        flash("Producto agregado correctamente", "success")
    except Exception as e:
        print(" ERROR AL INSERTAR:", e)
        flash("Error al agregar producto: " + str(e), "danger")
    return redirect(url_for('gestionproducto'))

# Eliminar producto
@app.route('/eliminar/<int:id>')
def eliminar_producto(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM producto WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Producto eliminado", "info")
    return redirect(url_for('gestionproducto'))

@app.route('/editar/<int:id>', methods=['POST'])
def editar_producto(id):
    cursor = mysql.connection.cursor()
    try:
        datos = (
            request.form['codigo'],
            request.form['nombre'],
            request.form['categoria'],
            int(request.form['cantidad']),
            float(request.form['precio_compra']),
            float(request.form['precio_venta']),
            request.form.get('proveedor'),
            request.form.get('fecha_compra'),
            request.form.get('fecha_vencimiento'),
            id
        )
        cursor.execute("""
            UPDATE producto SET
                codigo=%s, nombre=%s, categoria=%s, cantidad=%s,
                precio_compra=%s, precio_venta=%s, proveedor=%s,
                fecha_compra=%s, fecha_vencimiento=%s
            WHERE id=%s
        """, datos)
        mysql.connection.commit()
        flash("Producto actualizado correctamente", "success")
    except Exception as e:
        flash("Error al actualizar producto: " + str(e), "danger")
    finally:
        cursor.close()
    return redirect(url_for('gestionproducto'))


@app.route('/listaproducto', methods=['GET', 'POST'])
def listaproducto():
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        datos = (
            request.form['codigo'],
            request.form['nombre'],
            request.form['categoria'],
            int(request.form['cantidad']),
            float(request.form['precio_compra']),
            float(request.form['precio_venta']),
            request.form.get('proveedor'),
            request.form.get('fecha_compra'),
            request.form.get('fecha_vencimiento')
        )
        cursor.execute("""
            INSERT INTO producto (
                codigo, nombre, categoria, cantidad,
                precio_compra, precio_venta, proveedor,
                fecha_compra, fecha_vencimiento
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, datos)
        mysql.connection.commit()

    cursor.execute("SELECT * FROM producto")
    productos = cursor.fetchall()
    cursor.close()
    return render_template('listaproducto.html', productos=productos)

@app.route('/usuario')
def usuario():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nombre, email, password FROM usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('usuario.html', usuarios=usuarios)


@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/baseadmin')
def baseadmin():
    return render_template('baseadmin.html')


@app.route('/admin')
def admin():
    if 'logueado' in session:
        if session.get('id_rol') == 1:
            return render_template('admin.html')
        elif session.get('id_rol') == 2:
            return render_template('usuario.html')
        else:
            flash('Rol no reconocido', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('login'))
    

@app.route('/logout')
def logout():
    session.clear()  # Elimina todos los datos de sesión
    flash('Sesión cerrada correctamente', 'info')  # Mensaje opcional
    return redirect(url_for('login'))  # Redirige al login

if __name__ == '__main__':
    app.run(debug = True, port=8000)  # ejecutar la aplicación en modo depuración