curl http://localhost:55127/hello
echo ''
curl -X GET http://localhost:55127/v1
echo ''
curl -X POST http://localhost:55127/v1 -d {a:b}
echo ''
curl -X put http://localhost:55127/v1 -d {a:b}
echo ''
curl -X delete http://localhost:55127/v1 -d {a:b}
echo ''

