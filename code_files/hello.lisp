; init memory
(alloc_str hello "Hello, world!")
(alloc_num addr 0)
(alloc_num len 0)

; print "Hello, world!"
(set addr hello)
(set len (get_by_addr addr))
(while (get_val len) do
    (set len (- (get_val len) 1))
    (set addr (+ (get_val addr) 1))
    (output (get_by_addr addr))
)
