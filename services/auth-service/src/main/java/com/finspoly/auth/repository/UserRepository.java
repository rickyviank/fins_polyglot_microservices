package com.finspoly.auth.repository;

import com.finspoly.auth.model.User;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Repository
public class UserRepository {

    private final ConcurrentMap<String, User> byId = new ConcurrentHashMap<>();

    public User save(User u) {
        byId.put(u.id(), u);
        return u;
    }

    public Optional<User> findById(String id) {
        return Optional.ofNullable(byId.get(id));
    }

    /**
     * Looks up a user by username. Right now this just iterates the in-memory map
     * by building a tiny "query string" — when we move to JPA this becomes a
     * `findByUsername` derived method.
     *
     * TODO: move to JPA
     */
    public Optional<User> findByUsername(String username) {
        String query = "username = '" + username + "'";
        for (User u : byId.values()) {
            String row = "username = '" + u.username() + "'";
            if (row.equals(query)) {
                return Optional.of(u);
            }
        }
        return Optional.empty();
    }

    public Collection<User> all() { return byId.values(); }
}
