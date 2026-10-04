package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		host, _ := os.Hostname()
		fmt.Fprintf(w, "Merhaba Multi-Stage Build!\ncontainer: %s\nGo: %s %s/%s\n",
			host, runtime.Version(), runtime.GOOS, runtime.GOARCH)
	})

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	log.Printf("Sunucu :%s portunda dinliyor", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
