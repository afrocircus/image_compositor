__author__ = 'Natasha Kelkar'
import sys
from PIL import Image
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class ColorSwatch(QtGui.QWidget):
    '''
    Color Swatch widget: Creates a colored rectangle of size 10x10.
    '''
    def __init__(self, rgbColor):
        super(ColorSwatch,self).__init__()
        layout = QtGui.QHBoxLayout()
        self.colorLabel = QtGui.QLabel()
        self.createColorSwatch(rgbColor)
        layout.addWidget(self.colorLabel)
        self.setLayout(layout)

    def createColorSwatch(self, rgbColor):
        '''
        Creates a QPixmap object, draws a rectangle and assigns
        it to a QLabel object.
        :param rgbColor: Color of the swatch
        :return: nothing
        '''
        paintChip = QtGui.QPixmap(10,10)
        painter = QtGui.QPainter()
        painter.begin(paintChip)
        painter.setBrush(QtGui.QColor(rgbColor[0],rgbColor[1],rgbColor[2]))
        painter.drawRect(0,0,10,10)
        painter.end()
        self.colorLabel.setPixmap(paintChip)

class ImageLoadWidget(QtGui.QWidget):
    '''
    Creates a widget that contains an image, and a file browser.
    '''
    request = QtCore.pyqtSignal(object)

    def __init__(self, imageName):
        '''
        Creates the elements of the widget.
        :param imageName: Name of Image to load.
        '''
        super(ImageLoadWidget, self).__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.imLabel = QtGui.QLabel()
        self.imLabel.setScaledContents(True)
        self.layout.addWidget(self.imLabel)
        self.image = QImage(imageName)
        self.setImage(imageName)
        self.imLabel.setFixedSize(400,224)
        self.rgbColor = (0,255,0)

        hLayout = QtGui.QHBoxLayout()
        fileLabel = QtGui.QLabel('Filename')
        hLayout.addWidget(fileLabel)
        self.fileEdit = QtGui.QLineEdit(imageName)
        self.fileEdit.setReadOnly(True)
        self.fileEdit.setToolTip('Click to select another image')
        self.fileEdit.mousePressEvent = self.openFileDialog
        hLayout.addWidget(self.fileEdit)
        self.layout.addLayout(hLayout,1,0)

    def openFileDialog(self, event):
        '''
        Opens a file browser when the text box is clicked.
        :param event: Event triggered when the text box is clicked.
        :return:
        '''
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open File",
            QtCore.QDir.currentPath())
        self.fileEdit.setText(str(filename))
        self.setImage(filename)

    def setImage(self, imageName):
        '''
        Sets the QLabel with the QImage.
        '''
        self.image = QImage(imageName)
        self.imLabel.setPixmap(QtGui.QPixmap(self.image))

    def setImageMouseEvent(self):
        '''
        Creates a mouse press event on the image label.
        Changes the cursor to CrossCursor when hovering over the image.
        '''
        self.imLabel.setCursor(QtGui.QCursor(Qt.CrossCursor))
        self.imLabel.mousePressEvent = self.recordPixelData

    def recordPixelData(self, event):
        '''
        Records the RGB value of the pixel selected by the mouse pointer.
        :param event: Event triggered on mouse press.
        :return:
        '''
        position = QPoint( event.pos().x(),  event.pos().y())
        color = QColor.fromRgb(self.image.pixel( position ) )
        if color.isValid():
            self.rgbColor = color.getRgb()
        # Emits a signal when the color is recorded. Passes the color as an argument.
        self.request.emit(self.rgbColor)

    def getRGBColor(self):
        '''
        :return: The RGB color value type (int,int,int)
        '''
        return self.rgbColor

    def getFilePath(self):
        '''
        :return: The file selected by the user.
        '''
        return self.fileEdit.text()

class ImageCompositor(QtGui.QMainWindow):
    '''
    Main Application Class.
    '''
    def __init__(self):
        '''
        Basic UI setup.
        '''
        super(ImageCompositor, self).__init__()
        self.setWindowTitle('Image Compositor')
        window = QtGui.QWidget()
        self.centralLayout = QtGui.QHBoxLayout()
        window.setLayout(self.centralLayout)
        self.setCentralWidget(window)
        self.setupUI()

    def setupUI(self):
        '''
        Creating the UI elements.
        '''

        # Creating the Image Viewer
        viewerBox = QtGui.QGroupBox('Image Viewer')
        vLayout = QtGui.QVBoxLayout()
        # Loading Default Images.
        self.bgWidget = ImageLoadWidget('images/bg/background2.jpg')
        self.fgWidget = ImageLoadWidget('images/fg/cat1.jpg')
        self.fgWidget.setImageMouseEvent()
        vLayout.addWidget(self.fgWidget)
        vLayout.addWidget(self.bgWidget)
        viewerBox.setLayout(vLayout)
        self.centralLayout.addWidget(viewerBox)

        # Creating the Image Control UI.
        ctrBox = QtGui.QGroupBox('Image Controls')
        vLayout = QtGui.QVBoxLayout()
        compButton = QtGui.QPushButton('Composite and Save')
        compButton.clicked.connect(self.composite)

        ctrLayout = QtGui.QGridLayout()
        ctrLayout.addWidget(QtGui.QLabel('Select Color'),0,0)
        colorSwatch = ColorSwatch(self.fgWidget.getRGBColor())
        # Listens for color change event. Changes color of swatch based on mouse click.
        self.fgWidget.request.connect(colorSwatch.createColorSwatch)
        ctrLayout.addWidget(colorSwatch,0,1)

        self.slider = QtGui.QSlider(Qt.Horizontal)
        self.slider.setRange(0,150)
        self.slider.setValue(100)
        ctrLayout.addWidget(QtGui.QLabel('Select Threshold'),1,0)
        ctrLayout.addWidget(self.slider,1,1)
        ctrLayout.addWidget(compButton,2,0)
        ctrBox.setLayout(ctrLayout)
        vLayout.addWidget(ctrBox)
        vLayout.addItem(QtGui.QSpacerItem(40,20,QSizePolicy.Minimum,QSizePolicy.Expanding))
        self.centralLayout.addLayout(vLayout)

    def composite(self):
        '''
        Compositing function. Reads pixel values from Image.
        Replaces pixels of foreground image with those of background image
        based on color selected and threshold value.
        '''

        outputImage = QtGui.QFileDialog.getSaveFileName(self, "Save File",
                      QtCore.QDir.currentPath(),'*.jpg')

        if outputImage:
            image1 = Image.open(str(self.fgWidget.getFilePath()))
            image2 = Image.open(str(self.bgWidget.getFilePath()))

            # Dictionary of image pixels
            # eg. pix1[0,0] = (0,255,0)
            pix1 = self.getPixelArray(image1)
            pix2 = self.getPixelArray(image2)

            threshold = self.slider.value()
            rgbColor = self.fgWidget.getRGBColor()

            # Replace pixels in image 1 with image 2 if they lie in the specified range.
            for x,y in pix1:
                r = pix1[x,y][0]
                g = pix1[x,y][1]
                b = pix1[x,y][2]
                if (rgbColor[0]-threshold) <= r <= (rgbColor[0]+threshold) and \
                   (rgbColor[1]-threshold) <= g <= (rgbColor[1]+threshold) and \
                   (rgbColor[2]-threshold) <= b <= (rgbColor[2]+threshold):
                    pix1[x,y] = pix2[x,y]

            # Create a new composite image
            compImage = Image.new('RGB', image1.size)
            for x,y in pix1:
                compImage.putpixel((x,y),pix1[x,y])

            # Save the new composite image and show in UI.
            compImage.save(str(outputImage))
            self.fgWidget.setImage(str(outputImage))

    def getPixelArray(self, image):
        '''
        Creates a dictionary of pixel values
        :param image: PIL Image object to get pixel values from.
        :return:
        '''
        size = image.size
        pix = dict()
        for x in xrange(0, size[0]):
            for y in xrange(0, size[1]):
                pix[x,y] = image.getpixel((x,y))
        return pix



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    gui = ImageCompositor()
    gui.show()
    app.exec_()