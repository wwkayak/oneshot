
from xml.etree import ElementTree

feedSpeedFile = os.path.join(datadir, "feed-speed.xml")

class FeedsAndSpeeds:
    self.stockMaterialList = list()
    self.toolMaterialList = list()
    def loadFeedsAndSpeeds(self):
        """ Load machine speeds and feeds data from an XML file.
        
            Allows for a speeds and feeds table to be
            defined in an external file. The builtin getattr() method
            is necessary because XML only contains the "name" of 
            the types and values. (the word 'int', not an actual int())
        """
        
        treeRoot = ElementTree.parse(feedSpeedFile)
        cuttingDataList = treeRoot.getiterator(tag='cuttingData')
        self.columnType = [getattr(__builtin__, col.get('type')) 
                            for col in cuttingDataList[0]]
        self.feedSpeedStore = gtk.ListStore(self.columnType[0], 
                                            self.columnType[1], 
                                            self.columnType[2], 
                                            self.columnType[3], 
                                            self.columnType[4])
        self.columnNames = [col.tag for col in cuttingDataList[0]]
        
        #XML shit needs to go, use JSON (need nesting)
        for cuttingDataRow in cuttingDataList:
            r = list()
            for setting in cuttingDataRow:
                r.append(getattr(__builtin__,
                                 setting.get('type'))(setting.text))
                if setting.tag == 'stockMaterial':
                    if setting.text not in self.stockMaterialList:
                        self.stockMaterialList.append(setting.text)
                if setting.tag == 'toolMaterial':
                    if setting.text not in self.toolMaterialList:
                        self.toolMaterialList.append(setting.text)
            self.feedSpeedStore.append(r)

    def addFeedsAndSpeeds(self):
        self.stockCombobox = self.builder.get_object("stock_combobox")
        self.toolCombobox = self.builder.get_object("tool_combobox")
        self.feedSpeedView = self.builder.get_object("feedSpeedView")
        self.feedSpeedView.set_model(self.feedSpeedStore) 
        for col, name, coltype in zip(self.feedSpeedView.get_columns(), 
                                      self.columnNames, 
                                      self.columnType):
            col.set_title(name)
            if coltype == float:
                cell = gtk.CellRendererText()
                cell.set_property('xalign', 1.0)
                col.clear()
                col.pack_start(cell)
                col.set_cell_data_func(cell, self.format_floats)

        [self.stockCombobox.append_text(mat) for mat in self.stockMaterialList]
        self.stockCombobox.set_active(0)#glade bug fix?
        [self.toolCombobox.append_text(mat) for mat in self.toolMaterialList] 
        self.toolCombobox.set_active(0)#glade bug fix?   
        self.sfmEntry = self.builder.get_object("sfm_value")
        self.iptEntry = self.builder.get_object("ipt_value")
