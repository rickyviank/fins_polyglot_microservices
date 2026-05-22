FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY target/transaction-service-*.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java","-jar","/app/app.jar"]
