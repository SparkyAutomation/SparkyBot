# styles.py

stylesheet = """
    /*-----QWidget-----*/
    QWidget {
        background-color: qlineargradient(spread:repeat, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(27, 39, 50, 255),stop:1 rgba(47, 53, 74, 255));
        color: #000000;
    }

    /*-----QLabel-----*/
    QLabel {
        background-color: transparent;
        color: #c2c7d5;
        font-size: 25px;
    }

    /*-----QPushButton-----*/
    QPushButton {
        background-color: qlineargradient(spread:pad, x1:0, y1:0.511, x2:1, y2:0.511, stop:0 rgba(0, 172, 149, 255),stop:0.995192 rgba(54, 197, 177, 255));
        color: #fff;
        font-size: 30px;
        font-weight: bold;
        border: none;
        border-radius: 3px;
        padding: 5px;
        outline: none;
    }
    
    QPushButton:hover {
        background-color: qlineargradient(spread:pad, x1:0, y1:0.511, x2:1, y2:0.511, stop:0 rgba(0, 207, 179, 255),stop:1 rgba(70, 255, 230, 255));
    }

    QPushButton::pressed {
        background-color: qlineargradient(spread:pad, x1:0, y1:0.511, x2:1, y2:0.511, stop:0 rgba(0, 207, 179, 255),stop:1 rgba(70, 255, 230, 255));
    }
    
    /*-----QSlider-----*/
    QSlider::groove:horizontal {
        border: 1px solid #999999;
        height: 8px;
        background: #242424;
        margin: 2px 0;
        border-radius: 4px;
    }

    QSlider::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #b7b7b7, stop:1 #6b6b6b);
        border: 1px solid #5c5c5c;
        width: 30px; /* Adjust the width */
        height: 100px; /* Adjust the height */
        margin: -11px 0; /* Adjust the margin */
        border-radius: 5px; /* Adjust the border-radius */
    }

    QSlider::handle:horizontal:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #dadbde, stop:1 #888888);
        border: 1px solid #7c7c7c;
    }

     /*-----QTableView & QTableWidget-----*/
    QTableView {
        background-color: #232939;
        border: 1px solid gray;
        color: #f0f0f0;
        gridline-color: #232939;
        outline: 0;
    }

    QTableView::disabled {
        background-color: #242526;
        border: 1px solid #32414B;
        color: #656565;
        gridline-color: #656565;
        outline: 0;
    }
    

    QTableView::item:hover {
        background-color: #606060;
        color: #f0f0f0;
    }

    QTableView::item:selected {
        background-color: #0ab19a;
        color: #F0F0F0;
    }

    QTableView::item:selected:disabled {
        background-color: #1a1b1c;
        border: 2px solid #525251;
        color: #656565;
    }

    QTableCornerButton::section {
        background-color: #343a49;
        color: #fff;
    }

    QHeaderView::section {
        color: #fff;
        border-top: 0px;
        border-bottom: 1px solid gray;
        border-right: 1px solid gray;
        background-color: #343a49;
        margin-top: 1px;
        margin-bottom: 1px;
        padding: 5px;
    }

    QHeaderView::section:disabled {
        background-color: #525251;
        color: #656565;
    }

    QHeaderView::section:checked {
        color: #fff;
        background-color: #0ab19a;
    }

    QHeaderView::section:checked:disabled {
        color: #656565;
        background-color: #525251;
    }

    QHeaderView::section::vertical::first,
    QHeaderView::section::vertical::only-one {
        border-top: 1px solid #353635;
    }

    QHeaderView::section::vertical {
        border-top: 1px solid #353635;
    }

    QHeaderView::section::horizontal::first,
    QHeaderView::section::horizontal::only-one {
        border-left: 1px solid #353635;
    }

    QHeaderView::section::horizontal {
        border-left: 1px solid #353635;
    }
    
    /*-----QTextEdit-----*/
    QTextEdit {
        background-color: #c2c7d5;
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 2px;
        padding: 3px;
        font-size: 16px; 
    }

    QTextEdit:hover {
        background-color: #c2c7d5;
    }

    QTextEdit:focus {
        background-color: #c2c7d5;
    }

    QTextEdit::disabled {
        background-color: #c2c7d5;
        color: #656565;
    }

    QTextEdit::placeholder {
        color: #656565;
    }
    /*-----QCheckBox-----*/
    QCheckBox {
        background-color: transparent;
        color: #fff;
        font-size: 10px;
        font-weight: bold;
        border: none;
        border-radius: 5px;
    }

    QCheckBox::indicator {
        color: #b1b1b1;
        background-color: #323232;
        border: 1px solid darkgray;
        width: 12px;
        height: 12px;
    }

    QCheckBox::indicator:checked {
        image: url("./ressources/check.png");
        background-color: qlineargradient(spread:pad, x1:0, y1:0.511, x2:1, y2:0.511, stop:0 rgba(0, 172, 149, 255),stop:0.995192 rgba(54, 197, 177, 255));
        border: 1px solid #607cff;
    }

    QCheckBox::indicator:unchecked:hover {
        border: 1px solid #08b099;
    }

    QCheckBox::disabled {
        color: #656565;
    }

    QCheckBox::indicator:disabled {
        background-color: #656565;
        color: #656565;
        border: 1px solid #656565;
    }

    /*-----QLineEdit-----*/
    QLineEdit {
        background-color: #c2c7d5;
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 2px;
        padding: 3px;
    }

    /*-----QListView-----*/
    QListView {
        background-color: qlineargradient(spread:pad, x1:1, y1:0, x2:1, y2:1, stop:0 rgba(50, 61, 80, 255),stop:1 rgba(44, 49, 69, 255));
        color: #fff;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid #191919;
    }

    QListView::item {
        color: #31cecb;
        background-color: #454e5e;
        border: none;
        padding: 5px;
        border-radius: 0px;
        padding-left: 10px;
        height: 42px;
    }

    QListView::item:selected {
        color: #31cecb;
        background-color: #454e5e;
    }

    QListView::item:!selected {
        color: white;
        background-color: transparent;
        border: none;
        padding-left: 10px;
    }

    QListView::item:!selected:hover {
        color: #bbbcba;
        background-color: #454e5e;
        border: none;
        padding-left: 10px;
    }

    /*-----QTreeView-----*/
    QTreeView {
        background-color: #232939;
        show-decoration-selected: 0;
        color: #c2c8d7;
    }

    QTreeView::item {
        border-top-color: transparent;
        border-bottom-color: transparent;
    }

    QTreeView::item:hover {
        background-color: #606060;
        color: #fff;
    }

    QTreeView::item:selected {
        background-color: #0ab19a;
        color: #fff;
    }

    QTreeView::item:selected:active {
        background-color: #0ab19a;
        color: #fff;
    }

    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {
        image: url(://tree-closed.png);
    }

    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children:has-siblings {
        image: url(://tree-open.png);
    }


    /*-----QScrollBar-----*/
    QScrollBar:horizontal {
        background-color: transparent;
        height: 8px;
        margin: 0px;
        padding: 0px;
    }

    QScrollBar::handle:horizontal {
        border: none;
        min-width: 100px;
        background-color: #56576c;
    }

    QScrollBar::add-line:horizontal, 
    QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, 
    QScrollBar::sub-page:horizontal {
        width: 0px;
        background-color: transparent;
    }

    QScrollBar:vertical {
        background-color: transparent;
        width: 8px;
        margin: 0;
    }

    QScrollBar::handle:vertical {
        border: none;
        min-height: 200px;
        background-color: #56576c;
    }

    QScrollBar::add-line:vertical, 
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, 
    QScrollBar::sub-page:vertical {
        height: 0px;
        background-color: transparent;
    }
"""
