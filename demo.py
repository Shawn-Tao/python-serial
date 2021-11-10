    def receiving(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                print(time.time(), addr, data, "recv-ok")
                self.sigRecvMsg.emit([data, addr])
            except Exception as e:
                print(e)
                #time.sleep(0.1)

            
    def sending(self):
        while True:
            if self.mqueue:               
                try:
                    #with self.lock:
                    payload, addr = self.mqueue.popleft()
                    print(len(self.mqueue), tuple(addr), payload,"send-ok")
                    self.sock.sendto(payload, tuple(addr))
                except Exception as e:
                    print(e)
                    #time.sleep(0.1)
            else:
                time.sleep(0.001)
                
    def file2generator(self, fname, sender, uid, end):
        header = b"\x08\x00\x00"
        ack_uid = int.to_bytes(int.from_bytes(uid, "big")+1, 2, "big")
        i = 0
        UPDATEING = True
        try:
            with open(fname, "rb") as f:            
                while UPDATEING:
                    data = f.read(5)
                    if not data:
                        data = b" " * 5
                        uid = end
                        UPDATEING = False
                    elif len(data) < 5:
                        data += b" "*(5-len(data))
                        uid = end
                        UPDATEING = False
                    else:
                        pass
                    msg = header + uid + struct.pack("<H", i) + data \
                            + crc8(uid[1:] + struct.pack("<H", i) + data)
                    #self.upload(msg)
                    self.add_cmd_to_queue(msg)
                    
                    try:
                        counter = 0
                        timer = QTimer()
                        timer.timeout.connect(lambda :self.add_cmd_to_queue(msg))
                        timer.start(self._config.get("timeout", 3)*1000)
                        while True: 
                            if not sender.isChecked():
                                UPDATEING = False
                                break       
                            logger.debug("Updateing..." + str(counter) + ":" +msg.hex())            
                            ack = (yield msg)
                            print("ack", ack[5:13], len(ack[5:13]), "\n", "msg", msg[5:13], len(msg[5:13]))
                            if ack and ack[3:5] == ack_uid \
                                and ack[5:13] == msg[5:13]:
                                counter += 1
                                if ack_uid == b"\x07\x21":
                                    if counter == self._config.get("sensors", 1):
                                        break
                                    else:
                                        continue
                                else:
                                    break
                    except Exception as e:
                        logger.exception(e)
                    finally:
                        i += 1
                        timer.stop()
        except Exception as e:
            logger.exception(e)
            