import os
import glob
from flask import Flask, flash, request, redirect, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
##
from pypdf import PdfReader, PdfWriter
import subprocess
import pymupdf
##

##

app=Flask(__name__,  template_folder='template')

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024   ##  MB

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, 'uploads')
DOWNLOAD_FOLDER = os.path.join(path, 'downloads')


# Make directory if uploads is not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
if not os.path.isdir(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set([ 'pdf'])

def download_file(directory, file):     
        # Flask's send_from_directory to send the file to the client
        return send_file(directory, file , as_attachment=True)

@app.route('/downloads', methods=['GET','POST'])
def downloadFile ():
    filepath=os.path.join(app.config['UPLOAD_FOLDER']) 
    print(filepath,' === ',compress_filename) 
    #For windows you need to use drive name [ex: F:/Example.pdf]    
    path = os.path.join(filepath,compress_filename)
    return send_file(path, as_attachment=True)

@app.route('/downloads_image', methods=['GET','POST'])
def downloadFile_2 ():
    filepath=os.path.join(app.config['UPLOAD_FOLDER'])
    print(filepath,' === ',compress_image_filename)
    path = os.path.join(filepath,compress_image_filename)
    return send_file(path, as_attachment=True)

@app.route('/delete', methods=['GET','POST'])
def Delete ():
    folder=app.config['UPLOAD_FOLDER']
    files=glob.glob(folder+'/*')
    print(' folder : ',folder, ' ==>', files)
    for f in files:
        os.remove(f)
    flash(' Data successfully removed. ')

    return render_template('processing.html')


### compression
def compress_file(input_file: str):
    output_file=input_file.split('/')[len(input_file.split('/'))-1]
    output_file=output_file+'_lossless_compressed.pdf'

    reader = PdfReader(os.path.join(app.config['UPLOAD_FOLDER'],input_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for page in writer.pages:
        # ⚠️ This has to be done on the writer, not the reader!
        page.compress_content_streams()  # This is CPU intensive!

    with open(os.path.join(app.config['UPLOAD_FOLDER'],output_file), "wb") as f:
        writer.write(f)
    

    return output_file

def compress_image_on_file(input_file: str):
    output_file=input_file.split('/')[len(input_file.split('/'))-1]
    output_file=output_file+'_image_compressed.pdf'
    reader = PdfReader(os.path.join(app.config['UPLOAD_FOLDER'],input_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for page in writer.pages:
        for img in page.images:
            img.replace(img.image, quality=80)

    with open(os.path.join(app.config['UPLOAD_FOLDER'],output_file), "wb") as f:
        writer.write(f)
    

    return output_file

def compress_ghostedscript_file(input_file: str):

    output_file=input_file.split('/')[len(input_file.split('/'))-1]
    output_file=output_file+'_gs_compressed.pdf'
    output_folder = output_file

    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)


    input_path = input_file
    output_path = output_folder
    subprocess.call(['gswin64c', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS=/screen', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    '-sOutputFile=' + os.path.join(app.config['DOWNLOAD_FOLDER'],output_path), os.path.join(app.config['UPLOAD_FOLDER'],input_path)])

    

    return None

def compress_ghostedscript_w_option_file(input_file: str, arg1: str):
    print(' arg1 : ',arg1)
    output_file=input_file.split('/')[len(input_file.split('/'))-1]
    output_file=output_file+'_gs_'+arg1.replace('/','')+'_compressed.pdf'
    output_folder = output_file

    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)


    input_path = input_file
    output_path = output_folder
    print(' input : ',os.path.join(app.config['UPLOAD_FOLDER'],output_path))
    print(' output : ',os.path.join(app.config['DOWNLOAD_FOLDER'],output_path))

    subprocess.call(['gswin64c', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                    '-dPDFSETTINGS='+arg1+'', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    '-sOutputFile=' + os.path.join(app.config['DOWNLOAD_FOLDER'],output_path), os.path.join(app.config['UPLOAD_FOLDER'],input_path)])



    return None


def compress_pymupdf(input_file):
    output_file=input_file.split('/')[len(input_file.split('/'))-1]
    output_file=output_file+'_image_compressed.pdf'
    input_path=os.path.join(app.config['UPLOAD_FOLDER'],input_file)
    doc = pymupdf.open(input_path)

    doc.ez_save(os.path.join(app.config['UPLOAD_FOLDER'],output_file), deflate=True , deflate_images=True, deflate_fonts=True,  garbage=3, compression_effort=100,clean=True)
    doc.close()
    return output_file

###
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('processing.html')

@app.route('/', methods=['POST'])
def upload_file():
    global compress_filename, compress_image_filename
    if request.method == 'POST':

        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('files[]')

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        flash('File(s) successfully uploaded and pressed => Go ahead download them all. ')
        print(' Compressing file ')
        compress_filename=compress_file(filename)
        print(' Compressing image on file ')
        # compress_image_filename=compress_image_on_file(filename)
        compress_image_filename=compress_pymupdf(filename)
        # print(' ===> ',compress_image_filename)
        ##
        # compress_ghostedscript_w_option_file(filename, '/default')
        ##      


        return redirect('/')

if __name__ == "__main__":
    app.run(host='127.0.0.1',port=5000,debug=False,threaded=True)